import json
import logging
from datetime import datetime, timezone

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WaMarketingCampaign(models.Model):
    _name = "wa.marketing.campaign"
    _description = "WhatsApp Marketing Campaign"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        default=lambda self: _("New"),
        copy=False,
        readonly=True,
        tracking=True,
    )
    campaign_name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        default=lambda self: self.env.user,
        tracking=True,
    )

    send_mode = fields.Selection(
        [
            ("individual", "Individual"),
            ("bulk", "Bulk"),
        ],
        required=True,
        default="individual",
        tracking=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Single Recipient",
        tracking=True,
        help="Used mainly for individual mode.",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("quoted", "Quoted"),
            ("awaiting_approval", "Awaiting Approval"),
            ("approved", "Approved"),
            ("queued", "Queued"),
            ("sending", "Sending"),
            ("partial", "Partially Sent"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    objective = fields.Selection(
        [
            ("promotion", "Promotion"),
            ("new_product", "New Product"),
            ("awareness", "Awareness"),
            ("retention", "Retention"),
        ],
        default="promotion",
        required=True,
        tracking=True,
    )

    message = fields.Text(string="Campaign Message", tracking=True)
    creative_prompt = fields.Text(string="Creative Prompt", tracking=True)
    approved_asset_url = fields.Char(string="Approved Asset URL", tracking=True)

    # Structured creative input fields
    headline = fields.Char(string="Headline", size=50, tracking=True)
    subheadline = fields.Char(string="Subheadline", size=80, tracking=True)
    cta_text = fields.Char(string="CTA Text", size=25, tracking=True)
    visual_style = fields.Selection(
        [
            ("Modern", "Modern"),
            ("Bold", "Bold"),
            ("Luxury", "Luxury"),
            ("Minimal", "Minimal"),
            ("Fun", "Fun"),
        ],
        string="Visual Style",
        default="Modern",
        tracking=True,
    )
    additional_instructions = fields.Char(
        string="Additional Instructions",
        size=120,
        tracking=True,
    )
    use_product_images = fields.Boolean(
        string="Use Product Images",
        default=True,
        tracking=True,
    )
    brand_name = fields.Char(string="Brand Name", size=50, tracking=True)

    # Campaign CTA / conversion fields
    cta_action = fields.Selection(
        [
            ("none", "None"),
            ("add_to_cart", "Order Now Adds Featured Product To Cart"),
        ],
        string="Order Now Action",
        default="add_to_cart",
        tracking=True,
        help="What should happen when the user taps the Order Now button.",
    )
    cta_product_id = fields.Many2one(
        "product.product",
        string="Order Now Product",
        tracking=True,
        help="The promoted product that will be added to the customer's cart when the user taps Order Now.",
    )
    cta_quantity = fields.Integer(
        string="Order Now Quantity",
        default=1,
        tracking=True,
        help="How many units to add to the cart from the Order Now button.",
    )
    cta_button_text = fields.Char(
        string="Order Now Button Text",
        default="Order Now",
        size=25,
        tracking=True,
        help="Visible label is controlled in Meta template. This field is kept for reference only.",
    )

    # Edit-creative fields
    edit_instruction = fields.Char(string="Edit Instruction", size=200, tracking=True)
    edit_mode = fields.Selection(
        [
            ("EDIT_MODE_BGSWAP", "Background Swap / Product Preserve"),
            ("EDIT_MODE_INPAINT_INSERTION", "Insert / Add Elements"),
            ("EDIT_MODE_INPAINT_REMOVAL", "Remove Elements"),
            ("EDIT_MODE_OUTPAINT", "Outpaint / Extend Canvas"),
        ],
        string="Edit Mode",
        default="EDIT_MODE_BGSWAP",
        tracking=True,
    )
    preserve_product = fields.Boolean(
        string="Preserve Product",
        default=True,
        tracking=True,
    )
    negative_prompt = fields.Char(string="Negative Prompt", size=200, tracking=True)

    schedule_at = fields.Datetime(string="Schedule At")
    send_now = fields.Boolean(string="Send Immediately", default=True)
    media_type = fields.Selection(
        [
            ("image", "Image"),
            ("video", "Video"),
        ],
        default="image",
        required=True,
        tracking=True,
    )

    campaign_line_ids = fields.One2many(
        "wa.marketing.campaign.line",
        "campaign_id",
        string="Products",
    )
    recipient_line_ids = fields.One2many(
        "wa.marketing.campaign.recipient",
        "campaign_id",
        string="Recipients",
    )
    quote_ids = fields.One2many(
        "wa.marketing.quote",
        "campaign_id",
        string="Quotes",
    )
    job_ids = fields.One2many(
        "wa.marketing.job",
        "campaign_id",
        string="Jobs",
    )
    creative_ids = fields.One2many(
        "wa.marketing.creative",
        "campaign_id",
        string="Creatives",
    )

    latest_quote_id = fields.Many2one(
        "wa.marketing.quote",
        string="Latest Quote",
        readonly=True,
    )
    latest_job_id = fields.Many2one(
        "wa.marketing.job",
        string="Latest Job",
        readonly=True,
    )
    latest_creative_id = fields.Many2one(
        "wa.marketing.creative",
        string="Latest Creative",
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    quoted_amount = fields.Monetary(
        string="Quoted Amount",
        currency_field="currency_id",
        readonly=True,
        tracking=True,
    )

    total_products = fields.Integer(compute="_compute_counts", store=True)
    total_recipients = fields.Integer(compute="_compute_counts", store=True)
    delivered_count = fields.Integer(compute="_compute_job_metrics")
    failed_count = fields.Integer(compute="_compute_job_metrics")

    campaign_api_url = fields.Char(
        related="company_id.wa_campaign_api_url",
        readonly=True,
        store=False,
    )
    campaign_api_token = fields.Char(
        related="company_id.wa_campaign_api_token",
        readonly=True,
        store=False,
    )
    campaign_company_code = fields.Char(
        related="company_id.wa_campaign_company_code",
        readonly=True,
        store=False,
    )

    @api.depends("campaign_line_ids", "recipient_line_ids")
    def _compute_counts(self):
        for rec in self:
            rec.total_products = len(rec.campaign_line_ids)
            rec.total_recipients = len(rec.recipient_line_ids)

    @api.depends("job_ids.delivered_count", "job_ids.failed_count")
    def _compute_job_metrics(self):
        for rec in self:
            delivered = sum(rec.job_ids.mapped("delivered_count"))
            failed = sum(rec.job_ids.mapped("failed_count"))
            rec.delivered_count = delivered
            rec.failed_count = failed

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = seq.next_by_code("wa.marketing.campaign") or _("New")
        records = super().create(vals_list)
        records._default_cta_product_from_lines()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._default_cta_product_from_lines()
        return res

    @api.onchange("campaign_line_ids")
    def _onchange_campaign_line_ids_set_cta_product(self):
        self._default_cta_product_from_lines()

    def _default_cta_product_from_lines(self):
        for rec in self:
            if (
                rec.cta_action == "add_to_cart"
                and not rec.cta_product_id
                and len(rec.campaign_line_ids) == 1
            ):
                rec.cta_product_id = rec.campaign_line_ids.product_id.id

    def _parse_api_datetime(self, value):
        if not value:
            return False

        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            return False

        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

        return fields.Datetime.to_string(dt)

    def _check_ready_for_quote(self):
        for rec in self:
            if rec.media_type not in ("image", "video"):
                raise UserError(_("Media type must be Image or Video."))
            if not rec.campaign_line_ids:
                raise UserError(_("Add at least one product before requesting a quote."))
            if rec.send_mode == "individual":
                if not rec.partner_id and not rec.recipient_line_ids:
                    raise UserError(_("Set a single recipient or add one recipient line."))
            else:
                if not rec.recipient_line_ids:
                    raise UserError(_("Add recipient lines for bulk mode."))

    def _check_ready_for_send(self):
        for rec in self:
            if rec.state not in ("quoted", "awaiting_approval", "approved"):
                raise UserError(_("Campaign must be quoted/approved before sending."))
            if not rec.latest_quote_id:
                raise UserError(_("Request a quote first."))
            if not rec.approved_asset_url:
                raise UserError(_("Approve a creative first so the campaign has an asset to send."))
            if rec.cta_action == "add_to_cart":
                if not rec.cta_product_id:
                    raise UserError(_("Select an Order Now Product."))
                if rec.cta_quantity <= 0:
                    raise UserError(_("Order Now Quantity must be greater than zero."))

    def _build_quote_payload(self):
        self.ensure_one()
        recipients = self._get_recipient_payload()
        products = [
            {
                "product_id": line.product_id.id,
                "product_name": line.product_id.display_name,
                "menu_item": bool(line.is_menu_item),
                "image_url": line.image_url or "",
                "description": line.wa_description or "",
                "quantity": line.quantity,
            }
            for line in self.campaign_line_ids
        ]
        return {
            "campaign_ref": self.name,
            "campaign_name": self.campaign_name,
            "company_id": self.company_id.id,
            "company_code": self.company_id.wa_campaign_company_code or "",
            "send_mode": self.send_mode,
            "objective": self.objective,
            "media_type": self.media_type,
            "recipient_count": len(recipients),
            "recipients": recipients,
            "products": products,
            "message": self.message or "",
        }

    def _build_buttons_payload(self):
        self.ensure_one()

        order_now = {
            "action": "none",
            "product_id": None,
            "product_name": "",
            "qty": 0,
        }

        if self.cta_action == "add_to_cart" and self.cta_product_id:
            order_now = {
                "action": "add_to_cart",
                "product_id": self.cta_product_id.id,
                "product_name": self.cta_product_id.display_name or "",
                "qty": self.cta_quantity or 1,
            }

        view_menu = {
            "action": "view_menu",
        }

        return {
            "order_now": order_now,
            "view_menu": view_menu,
        }

    def _build_send_payload(self):
        self.ensure_one()
        return {
            "campaign_ref": self.name,
            "campaign_name": self.campaign_name,
            "quote_id": self.latest_quote_id.external_quote_id or "",
            "approved_creative_job_id": (
                self.latest_creative_id.external_creative_job_id if self.latest_creative_id else None
            ),
            "approved_asset_url": self.approved_asset_url or "",
            "send_mode": self.send_mode,
            "media_type": self.media_type,
            "message": self.message or "",
            "schedule_at": self.schedule_at.isoformat() if self.schedule_at else None,
            "recipients": self._get_recipient_payload(),
            "buttons": self._build_buttons_payload(),
        }

    def _get_headers(self):
        self.ensure_one()
        token = self.company_id.wa_campaign_api_token or ""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _get_base_url(self):
        self.ensure_one()
        base_url = (self.company_id.wa_campaign_api_url or "").rstrip("/")
        if not base_url:
            raise UserError(_("Set Campaign API URL on the company first."))
        return base_url

    def _get_recipient_payload(self):
        self.ensure_one()
        recipients = []

        if self.send_mode == "individual" and self.partner_id:
            partner_phone = (
                getattr(self.partner_id, "mobile", False)
                or getattr(self.partner_id, "phone", False)
                or ""
            )
            if partner_phone:
                recipients.append(
                    {
                        "partner_id": self.partner_id.id,
                        "name": self.partner_id.name or "",
                        "phone": partner_phone,
                    }
                )

        for line in self.recipient_line_ids:
            phone = line.mobile or line.phone or ""
            if phone:
                recipients.append(
                    {
                        "recipient_line_id": line.id,
                        "partner_id": line.partner_id.id if line.partner_id else None,
                        "name": line.partner_id.name if line.partner_id else "",
                        "phone": phone,
                    }
                )

        seen = set()
        deduped = []
        for item in recipients:
            phone = item.get("phone")
            if phone and phone not in seen:
                seen.add(phone)
                deduped.append(item)

        return deduped

    def action_request_quote(self):
        for rec in self:
            rec._check_ready_for_quote()
            payload = rec._build_quote_payload()
            url = f"{rec._get_base_url()}/api/campaigns/quote"

            _logger.warning("Campaign quote URL being used: %s", url)
            _logger.warning("Campaign quote payload: %s", json.dumps(payload, ensure_ascii=False))

            try:
                response = requests.post(
                    url,
                    headers=rec._get_headers(),
                    json=payload,
                    timeout=30,
                )
                _logger.warning("Quote response status: %s", response.status_code)
                _logger.warning("Quote response body: %s", response.text)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                _logger.exception("Quote request failed for campaign %s", rec.name)
                raise UserError(_("Quote request failed: %s") % str(exc))

            quote = self.env["wa.marketing.quote"].create(
                {
                    "campaign_id": rec.id,
                    "external_quote_id": data.get("quote_id"),
                    "amount": data.get("amount", 0.0),
                    "currency_code": data.get("currency", rec.currency_id.name),
                    "status": data.get("status", "quoted"),
                    "expires_at": rec._parse_api_datetime(data.get("expires_at")),
                    "breakdown_json": json.dumps(
                        data.get("breakdown", {}),
                        ensure_ascii=False,
                    ),
                    "raw_response_json": json.dumps(data, ensure_ascii=False),
                }
            )
            rec.latest_quote_id = quote.id
            rec.quoted_amount = quote.amount
            rec.state = "quoted"

    def action_generate_creative(self):
        for rec in self:
            if not rec.latest_quote_id:
                raise UserError(_("Request a quote first."))

            url = f"{rec._get_base_url()}/api/campaigns/generate-creative"
            payload = {
                "campaign_ref": rec.name,
                "quote_id": rec.latest_quote_id.external_quote_id or "",
                "creative_type": rec.media_type,
                "company_id": rec.company_id.id,
                "company_code": rec.company_id.wa_campaign_company_code or "",
                "objective": rec.objective or "",
                "message": rec.creative_prompt or rec.message or "",
                "headline": rec.headline or "",
                "subheadline": rec.subheadline or "",
                "cta_text": rec.cta_text or "",
                "visual_style": rec.visual_style or "Modern",
                "additional_instructions": rec.additional_instructions or "",
                "use_product_images": bool(rec.use_product_images),
                "brand_name": rec.brand_name or rec.company_id.name or "",
                "products": [
                    {
                        "product_id": line.product_id.id,
                        "product_name": line.product_id.display_name,
                        "image_url": line.image_url or "",
                        "description": line.wa_description or "",
                        "quantity": line.quantity,
                        "menu_item": bool(line.is_menu_item),
                    }
                    for line in rec.campaign_line_ids
                ],
            }

            _logger.warning("Generate creative URL: %s", url)
            _logger.warning(
                "Generate creative payload: %s",
                json.dumps(payload, ensure_ascii=False, default=str),
            )

            try:
                response = requests.post(
                    url,
                    headers=rec._get_headers(),
                    json=payload,
                    timeout=120,
                )
                _logger.warning("Generate creative status: %s", response.status_code)
                _logger.warning("Generate creative body: %s", response.text)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                _logger.exception("Creative generation failed for campaign %s", rec.name)
                raise UserError(_("Creative generation failed: %s") % str(exc))

            creative = self.env["wa.marketing.creative"].create(
                {
                    "campaign_id": rec.id,
                    "external_creative_job_id": data.get("creative_job_id"),
                    "creative_type": data.get("creative_type", rec.media_type),
                    "status": data.get("status", "completed"),
                    "prompt_text": data.get("prompt_text") or rec.creative_prompt or rec.message or "",
                    "asset_url": data.get("asset_url"),
                    "preview_url": data.get("preview_url"),
                    "raw_response_json": json.dumps(data, ensure_ascii=False),
                }
            )

            rec.latest_creative_id = creative.id

            if data.get("asset_url"):
                rec.state = "awaiting_approval"

    def action_edit_latest_creative(self):
        for rec in self:
            if not rec.latest_creative_id or not rec.latest_creative_id.external_creative_job_id:
                raise UserError(_("No latest creative found to edit."))

            if not rec.edit_instruction:
                raise UserError(_("Please enter an edit instruction first."))

            url = f"{rec._get_base_url()}/api/campaigns/edit-creative"
            payload = {
                "previous_creative_job_id": rec.latest_creative_id.external_creative_job_id,
                "instruction_text": rec.edit_instruction or "",
                "edit_mode": rec.edit_mode or "EDIT_MODE_BGSWAP",
                "preserve_product": bool(rec.preserve_product),
                "negative_prompt": rec.negative_prompt or "",
            }

            _logger.warning("Edit creative URL: %s", url)
            _logger.warning(
                "Edit creative payload: %s",
                json.dumps(payload, ensure_ascii=False, default=str),
            )

            try:
                response = requests.post(
                    url,
                    headers=rec._get_headers(),
                    json=payload,
                    timeout=180,
                )
                _logger.warning("Edit creative status: %s", response.status_code)
                _logger.warning("Edit creative body: %s", response.text)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                _logger.exception("Creative edit failed for campaign %s", rec.name)
                raise UserError(_("Creative edit failed: %s") % str(exc))

            creative = self.env["wa.marketing.creative"].create(
                {
                    "campaign_id": rec.id,
                    "external_creative_job_id": data.get("creative_job_id"),
                    "creative_type": data.get("creative_type", rec.media_type),
                    "status": data.get("status", "completed"),
                    "prompt_text": data.get("prompt_text") or rec.edit_instruction or "",
                    "asset_url": data.get("asset_url"),
                    "preview_url": data.get("preview_url"),
                    "raw_response_json": json.dumps(data, ensure_ascii=False),
                }
            )

            rec.latest_creative_id = creative.id

            if data.get("asset_url"):
                rec.state = "awaiting_approval"

        return True

    def action_approve_latest_creative(self):
        for rec in self:
            if not rec.latest_creative_id:
                raise UserError(_("No generated creative found."))

            rec.creative_ids.write({"is_approved": False})
            rec.latest_creative_id.write({"is_approved": True})

            rec.write(
                {
                    "approved_asset_url": rec.latest_creative_id.asset_url or "",
                    "state": "approved",
                }
            )

    def action_mark_awaiting_approval(self):
        self.write({"state": "awaiting_approval"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_send_campaign(self):
        for rec in self:
            rec._check_ready_for_send()

            approved_asset_url = rec.approved_asset_url or False
            if not approved_asset_url:
                raise UserError(
                    _(
                        "No approved asset URL found. Approve/select an image or video asset before sending."
                    )
                )

            payload = rec._build_send_payload()
            url = f"{rec._get_base_url()}/api/campaigns/send"

            _logger.warning("Campaign send URL being used: %s", url)
            _logger.warning("Campaign send payload: %s", json.dumps(payload, ensure_ascii=False))

            try:
                response = requests.post(
                    url,
                    headers=rec._get_headers(),
                    json=payload,
                    timeout=45,
                )
                _logger.warning("Send response status: %s", response.status_code)
                _logger.warning("Send response body: %s", response.text)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                _logger.exception("Send failed for campaign %s", rec.name)
                raise UserError(_("Campaign send failed: %s") % str(exc))

            job = self.env["wa.marketing.job"].create(
                {
                    "campaign_id": rec.id,
                    "external_job_id": data.get("job_id"),
                    "status": data.get("status", "queued"),
                    "send_mode": rec.send_mode,
                    "total_recipients": data.get(
                        "total_recipients", rec.total_recipients
                    ),
                    "accepted_count": data.get("accepted_count", 0),
                    "rejected_count": data.get("rejected_count", 0),
                    "raw_response_json": json.dumps(data, ensure_ascii=False),
                }
            )
            rec.latest_job_id = job.id
            rec.state = data.get("status", "queued")

    def action_refresh_job_status(self):
        for rec in self.filtered("latest_job_id"):
            job = rec.latest_job_id
            if not job.external_job_id:
                continue

            url = f"{rec._get_base_url()}/api/campaigns/jobs/{job.external_job_id}"

            _logger.warning("Campaign refresh URL being used: %s", url)

            try:
                response = requests.get(
                    url,
                    headers=rec._get_headers(),
                    timeout=20,
                )
                _logger.warning("Refresh response status: %s", response.status_code)
                _logger.warning("Refresh response body: %s", response.text)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                _logger.exception("Job refresh failed for campaign %s", rec.name)
                raise UserError(_("Job status refresh failed: %s") % str(exc))

            job.write(
                {
                    "status": data.get("status", job.status),
                    "accepted_count": data.get("accepted_count", job.accepted_count),
                    "rejected_count": data.get("rejected_count", job.rejected_count),
                    "delivered_count": data.get("delivered_count", job.delivered_count),
                    "failed_count": data.get("failed_count", job.failed_count),
                    "started_at": self._parse_api_datetime(data.get("started_at")),
                    "completed_at": self._parse_api_datetime(data.get("completed_at")),
                    "raw_response_json": json.dumps(data, ensure_ascii=False),
                }
            )
            rec.state = data.get("status", rec.state)

    def action_cancel(self):
        self.write({"state": "cancelled"})