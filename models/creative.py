from odoo import api, fields, models


class WaMarketingCreative(models.Model):
    _name = "wa.marketing.creative"
    _description = "WhatsApp Marketing Creative"
    _order = "id desc"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True,
    )

    campaign_id = fields.Many2one(
        "wa.marketing.campaign",
        string="Campaign",
        required=True,
        ondelete="cascade",
    )

    external_creative_job_id = fields.Char(
        string="External Creative Job ID",
        index=True,
    )

    creative_type = fields.Selection(
        [
            ("image", "Image"),
            ("video", "Video"),
        ],
        string="Creative Type",
        default="image",
        required=True,
    )

    version_no = fields.Integer(
        string="Version No",
        default=1,
    )

    status = fields.Char(
        string="Status",
        default="pending",
    )

    prompt_text = fields.Text(string="Prompt / Edit Instruction")
    asset_url = fields.Char(string="Asset URL")
    preview_url = fields.Char(string="Preview URL")
    is_approved = fields.Boolean(string="Approved", default=False)
    raw_response_json = fields.Text(string="Raw Response JSON")

    preview_html = fields.Html(
        string="Preview",
        compute="_compute_preview_html",
        sanitize=False,
    )

    @api.depends("external_creative_job_id", "creative_type", "campaign_id", "version_no")
    def _compute_name(self):
        for rec in self:
            campaign_name = rec.campaign_id.name or "Campaign"
            creative_type = rec.creative_type or "creative"
            version_label = f"v{rec.version_no or 1}"

            if rec.external_creative_job_id:
                rec.name = f"{rec.external_creative_job_id} ({version_label})"
            else:
                rec.name = f"{campaign_name} - {creative_type} ({version_label})"

    @api.depends("creative_type", "asset_url", "preview_url")
    def _compute_preview_html(self):
        for rec in self:
            media_url = rec.preview_url or rec.asset_url

            if not media_url:
                rec.preview_html = """
                    <div style="padding:16px; color:#666; font-size:14px;">
                        No preview available yet.
                    </div>
                """
                continue

            if rec.creative_type == "image":
                rec.preview_html = f"""
                    <div style="padding:12px;">
                        <img src="{media_url}"
                             style="max-width:100%; max-height:420px; border:1px solid #ddd; border-radius:8px; object-fit:contain;" />
                    </div>
                """
            elif rec.creative_type == "video":
                rec.preview_html = f"""
                    <div style="padding:12px;">
                        <video controls style="max-width:100%; max-height:420px; border:1px solid #ddd; border-radius:8px;">
                            <source src="{media_url}">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                """
            else:
                rec.preview_html = f"""
                    <div style="padding:12px;">
                        <a href="{media_url}" target="_blank">Open media</a>
                    </div>
                """