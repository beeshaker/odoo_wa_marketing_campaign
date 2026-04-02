import json
import logging
from datetime import datetime, timezone

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WaMarketingCampaignCallbacks(http.Controller):

    def _get_expected_token(self):
        token = request.env["ir.config_parameter"].sudo().get_param(
            "wa_marketing_campaign.odoo_callback_token",
            default="",
        )
        if token:
            return token

        company = request.env.company.sudo()
        return company.wa_campaign_api_token or ""

    def _is_authorized(self):
        auth_header = request.httprequest.headers.get("Authorization", "")
        token = self._get_expected_token()
        expected = f"Bearer {token}"
        return bool(token) and auth_header == expected

    def _parse_api_datetime(self, value):
        if not value:
            return False
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            return False

        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @http.route(
        "/wa_marketing_campaign/ping",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def ping(self, **kwargs):
        return request.make_response("wa_marketing_campaign callbacks loaded")

    @http.route(
        "/wa_marketing_campaign/callback/quote",
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def quote_callback(self, **kwargs):
        if not self._is_authorized():
            return {"ok": False, "error": "Invalid token"}

        data = request.jsonrequest or {}
        _logger.warning("Quote callback received: %s", json.dumps(data, ensure_ascii=False))

        campaign_ref = data.get("campaign_ref")
        external_quote_id = data.get("quote_id")

        if not campaign_ref or not external_quote_id:
            return {"ok": False, "error": "campaign_ref and quote_id are required"}

        campaign = request.env["wa.marketing.campaign"].sudo().search(
            [("name", "=", campaign_ref)],
            limit=1,
        )
        if not campaign:
            return {"ok": False, "error": "Campaign not found"}

        quote_vals = {
            "campaign_id": campaign.id,
            "external_quote_id": external_quote_id,
            "amount": data.get("amount", 0.0),
            "currency_code": data.get("currency", "KES"),
            "status": data.get("status", "quoted"),
            "expires_at": self._parse_api_datetime(data.get("expires_at")),
            "breakdown_json": json.dumps(data.get("breakdown", {}), ensure_ascii=False),
            "raw_response_json": json.dumps(data, ensure_ascii=False),
        }

        quote = request.env["wa.marketing.quote"].sudo().search(
            [("external_quote_id", "=", external_quote_id)],
            limit=1,
        )
        if quote:
            quote.write(quote_vals)
        else:
            quote = request.env["wa.marketing.quote"].sudo().create(quote_vals)

        campaign.sudo().write(
            {
                "latest_quote_id": quote.id,
                "quoted_amount": quote.amount,
                "state": "quoted",
            }
        )

        return {
            "ok": True,
            "campaign_ref": campaign_ref,
            "quote_id": external_quote_id,
        }

    @http.route(
        "/wa_marketing_campaign/callback/creative",
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def creative_callback(self, **kwargs):
        if not self._is_authorized():
            return {"ok": False, "error": "Invalid token"}

        data = request.jsonrequest or {}
        _logger.warning("Creative callback received: %s", json.dumps(data, ensure_ascii=False))

        campaign_ref = data.get("campaign_ref")
        creative_job_id = data.get("creative_job_id")
        creative_type = data.get("creative_type", "image")
        status = data.get("status", "creative_generated")
        asset_url = data.get("asset_url")
        preview_url = data.get("preview_url") or asset_url
        prompt_text = data.get("prompt_text") or data.get("prompt")

        if not campaign_ref:
            return {"ok": False, "error": "campaign_ref is required"}

        if not creative_job_id:
            return {"ok": False, "error": "creative_job_id is required"}

        campaign = request.env["wa.marketing.campaign"].sudo().search(
            [("name", "=", campaign_ref)],
            limit=1,
        )
        if not campaign:
            return {"ok": False, "error": "Campaign not found"}

        creative_model = request.env["wa.marketing.creative"].sudo()

        creative_vals = {
            "campaign_id": campaign.id,
            "external_creative_job_id": creative_job_id,
            "creative_type": creative_type,
            "status": status,
            "prompt_text": prompt_text,
            "asset_url": asset_url,
            "preview_url": preview_url,
            "is_approved": False,
            "raw_response_json": json.dumps(data, ensure_ascii=False),
        }

        creative = creative_model.search(
            [("external_creative_job_id", "=", creative_job_id)],
            limit=1,
        )

        if creative:
            creative.write(creative_vals)
        else:
            creative = creative_model.create(creative_vals)

        if status in ("creative_generated", "creative_ready", "completed", "approved"):
            campaign.sudo().write({"state": "awaiting_approval"})

        return {
            "ok": True,
            "campaign_ref": campaign_ref,
            "creative_job_id": creative_job_id,
            "creative_id": creative.id,
            "asset_url": creative.asset_url,
            "preview_url": creative.preview_url,
        }

    @http.route(
        "/wa_marketing_campaign/callback/send_job",
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def send_job_callback(self, **kwargs):
        if not self._is_authorized():
            return {"ok": False, "error": "Invalid token"}

        data = request.jsonrequest or {}
        _logger.warning("Send job callback received: %s", json.dumps(data, ensure_ascii=False))

        campaign_ref = data.get("campaign_ref")
        external_job_id = data.get("job_id")
        if not campaign_ref or not external_job_id:
            return {"ok": False, "error": "campaign_ref and job_id are required"}

        campaign = request.env["wa.marketing.campaign"].sudo().search(
            [("name", "=", campaign_ref)],
            limit=1,
        )
        if not campaign:
            return {"ok": False, "error": "Campaign not found"}

        job_model = request.env["wa.marketing.job"].sudo()
        job = job_model.search(
            [("external_job_id", "=", external_job_id)],
            limit=1,
        )

        vals = {
            "campaign_id": campaign.id,
            "external_job_id": external_job_id,
            "status": data.get("status", "queued"),
            "send_mode": campaign.send_mode,
            "total_recipients": data.get("total_recipients", campaign.total_recipients),
            "accepted_count": data.get("accepted_count", 0),
            "rejected_count": data.get("rejected_count", 0),
            "delivered_count": data.get("delivered_count", 0),
            "failed_count": data.get("failed_count", 0),
            "started_at": self._parse_api_datetime(data.get("started_at")),
            "completed_at": self._parse_api_datetime(data.get("completed_at")),
            "raw_response_json": json.dumps(data, ensure_ascii=False),
        }

        if job:
            job.write(vals)
        else:
            job = job_model.create(vals)

        campaign.write(
            {
                "latest_job_id": job.id,
                "state": data.get("status", campaign.state),
            }
        )

        return {"ok": True, "campaign_ref": campaign_ref, "job_id": external_job_id}

    @http.route(
        "/wa_marketing_campaign/callback/delivery",
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def delivery_callback(self, **kwargs):
        if not self._is_authorized():
            return {"ok": False, "error": "Invalid token"}

        data = request.jsonrequest or {}
        _logger.warning("Delivery callback received: %s", json.dumps(data, ensure_ascii=False))
        return {"ok": True}