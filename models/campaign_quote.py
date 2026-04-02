from odoo import fields, models


class WaMarketingQuote(models.Model):
    _name = "wa.marketing.quote"
    _description = "WhatsApp Marketing Quote"
    _order = "id desc"

    campaign_id = fields.Many2one(
        "wa.marketing.campaign",
        required=True,
        ondelete="cascade",
    )
    external_quote_id = fields.Char(string="External Quote ID", index=True)
    amount = fields.Float(string="Amount")
    currency_code = fields.Char(default="KES")
    status = fields.Char(default="quoted")
    expires_at = fields.Datetime()
    breakdown_json = fields.Text(string="Breakdown JSON")
    raw_response_json = fields.Text(string="Raw Response JSON")
