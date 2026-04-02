from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    wa_campaign_api_url = fields.Char(
        string="Campaign API URL",
        help="Base URL of the campaign microservice, e.g. http://127.0.0.1:8001",
    )
    wa_campaign_api_token = fields.Char(
        string="Campaign API Token",
        help="Bearer token used by the campaign microservice.",
    )
    wa_campaign_company_code = fields.Char(
        string="Campaign Company Code",
        help="Optional company code used by the campaign microservice.",
    )