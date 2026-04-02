from odoo import fields, models


class WaMarketingJob(models.Model):
    _name = "wa.marketing.job"
    _description = "WhatsApp Marketing Send Job"
    _order = "id desc"
   

    campaign_id = fields.Many2one(
        "wa.marketing.campaign",
        required=True,
        ondelete="cascade",
    )
    external_job_id = fields.Char(string="External Job ID", index=True)
    status = fields.Char(default="queued")
    send_mode = fields.Selection(
        [
            ("individual", "Individual"),
            ("bulk", "Bulk"),
        ]
    )
    total_recipients = fields.Integer(default=0)
    accepted_count = fields.Integer(default=0)
    rejected_count = fields.Integer(default=0)
    delivered_count = fields.Integer(default=0)
    failed_count = fields.Integer(default=0)
    started_at = fields.Datetime()
    completed_at = fields.Datetime()
    raw_response_json = fields.Text(string="Raw Response JSON")
