from odoo import fields, models


class WaMarketingCampaignLine(models.Model):
    _name = "wa.marketing.campaign.line"
    _description = "WhatsApp Marketing Campaign Product"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    campaign_id = fields.Many2one(
        "wa.marketing.campaign",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        "product.product",
        required=True,
        domain=[("product_tmpl_id.wa_is_menu_item", "=", True)],
    )

    product_tmpl_id = fields.Many2one(
        related="product_id.product_tmpl_id",
        store=True,
        readonly=True,
    )
    quantity = fields.Float(default=1.0)

    is_menu_item = fields.Boolean(
        related="product_tmpl_id.wa_is_menu_item",
        readonly=True,
        store=True,
    )
    wa_description = fields.Text(
        related="product_tmpl_id.wa_description",
        readonly=True,
        store=True,
    )
    wa_is_available = fields.Boolean(
        related="product_tmpl_id.wa_is_available",
        readonly=True,
        store=True,
    )
    image_url = fields.Char(
        related="product_tmpl_id.wa_menu_image_url",
        readonly=True,
        store=True,
    )
    list_price = fields.Float(
        related="product_id.lst_price",
        readonly=True,
        store=True,
    )
    marketing_note = fields.Char()
