"""Public looking glass: rate-limited ping/trace/route queries dispatched to a node.

Every query (and its outcome) is logged to the LGQuery table for audit. Browsers submitting the
form get the full page back; the in-page ``fetch`` (header ``X-Requested-With: fetch``) gets a small
JSON payload so the result can be swapped in without a reload.

For ``bird_protocols`` the backend additionally parses the raw ``birdc show protocols all <name>``
output into structured data (see ``app.lg.summary``) so the public LG page can render a rich BGP
session view (name, state, neighbor, channels v4/v6, import/export counts).
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.auth.session import current_user
from app.db.models import LGQuery, Node
from app.db.session import get_db
from app.lg.client import NodeClient
from app.lg.validation import validate_query_type, validate_target
from app.node_ws import node_runtime_context
from app.web.deps import client_ip, lg_rate_limiter, logger, query_enabled_nodes, render

router = APIRouter()


@router.get("/lg", response_class=HTMLResponse)
def looking_glass_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the looking-glass query form (the POST handler below runs the query)."""
    nodes = query_enabled_nodes(db).all()
    runtime = node_runtime_context(nodes)
    nodes_with_runtime = []
    for node in nodes:
        node_dict = {"id": node.id, "name": node.name, "location": node.location}
        node_dict["runtime"] = runtime.get(node.id, {})
        nodes_with_runtime.append(node_dict)
    return render(request, "lg.html", {"nodes": nodes_with_runtime}, user=current_user(request, db), active="lg")


def _parse_bird_protocols_output(output: str, target: str) -> dict:
    """Parse a BIRD protocols output string into the shape expected by the frontend.

    Returns ``{"mode": "list", "protocols": [...]}`` when ``target`` is empty (show all),
    or ``{"mode": "detail", ...}`` for a specific protocol. Falls back to ``None`` on error
    so the caller can decide whether to hide the parsed block.
    """
    try:
        from app.lg.summary import parse_bird_protocols_all, parse_bird_protocols_list
        if target:
            parsed = parse_bird_protocols_all(output)
            if isinstance(parsed, dict) and "error" not in parsed:
                parsed["mode"] = "detail"
                return parsed
        else:
            parsed_list = parse_bird_protocols_list(output)
            if parsed_list:
                return {"mode": "list", "protocols": parsed_list}
    except Exception as exc:  # never let parser kill the query
        logger.debug("LG bird_protocols parse failed: %s", exc)
    return None


@router.post("/lg", response_class=HTMLResponse)
async def looking_glass(
    request: Request,
    node_id: str = Form(...),
    query_type: str = Form(...),
    target: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    if not lg_rate_limiter.allow(client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="Too many looking glass queries. Please wait a moment and try again.",
        )
    node = query_enabled_nodes(db).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=400, detail="Unknown or disabled node")
    result_text = ""
    ok = False
    normalized_query_type = query_type
    normalized_target = target.strip()
    parsed_data = None
    try:
        normalized_query_type = validate_query_type(query_type)
        normalized_target = validate_target(normalized_query_type, target)
    except ValueError as exc:
        result_text = str(exc)
    else:
        try:
            result = await NodeClient().query(node, normalized_query_type, normalized_target)
            ok = bool(result.get("ok", False))
            raw_output = str(result.get("output", result.get("result", "")))
            result_text = raw_output
            # Enrich with structured BGP data when querying BIRD protocols.
            if normalized_query_type == "bird_protocols" and ok:
                parsed_data = _parse_bird_protocols_output(raw_output, normalized_target)
        except ValueError as exc:
            result_text = str(exc)
        except Exception as exc:
            logger.warning(
                "Looking glass query failed (node=%s, type=%s): %s",
                node.name,
                normalized_query_type,
                exc,
            )
            result_text = "Query failed: could not reach the looking glass node."
    user = current_user(request, db)
    db.add(
        LGQuery(
            user_id=user.id if user else None,
            node_id=node.id,
            query_type=normalized_query_type,
            target=normalized_target,
            ok=ok,
            result=result_text,
        )
    )
    db.commit()

    # In-page fetch: return just the outcome as JSON so the page can swap it in without a reload.
    if request.headers.get("x-requested-with", "").lower() == "fetch":
        payload: dict = {"ok": ok, "output": result_text, "query_type": normalized_query_type}
        if parsed_data is not None:
            payload["parsed"] = parsed_data
        return JSONResponse(payload)

    nodes = query_enabled_nodes(db).all()
    runtime = node_runtime_context(nodes)
    nodes_with_runtime = []
    for node in nodes:
        node_dict = {"id": node.id, "name": node.name, "location": node.location}
        node_dict["runtime"] = runtime.get(node.id, {})
        nodes_with_runtime.append(node_dict)
    template_data = {
        "nodes": nodes_with_runtime,
        "lg_result": result_text,
        "lg_ok": ok,
        "last_query": normalized_query_type,
        "last_target": normalized_target,
    }
    if parsed_data is not None:
        template_data["lg_parsed"] = parsed_data
    return render(
        request,
        "lg.html",
        template_data,
        user=user,
        active="lg",
    )
