# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from subprocess import call
from lxml import etree
from xml.dom import minidom
import xml.etree.ElementTree as ET
import types
import re
from odoo import fields, models, api, tools, _
from odoo.exceptions import Warning, UserError, ValidationError


class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.constrains('type', 'groups_id', 'inherit_id')
    def _check_groups(self):
        for view in self:
            if view._context.get('from_bi'):
                return
            else:
                return super()._check_groups()

class CustomFields(models.Model):
    _name = 'custom.fields'
    _description = "Custom Fields"

    def _get_fields_type(self):
        res = [('binary', 'binary'), ('boolean', 'boolean'), ('char', 'char'), ('date', 'date'),
               ('datetime', 'datetime'), ('float', 'float'), ('html', 'html'), ('integer', 'integer'),
               ('many2one', 'many2one'),('selection', 'selection'),
                ('text', 'text'),('monetary', 'monetary'),('many2one_reference','many2one_reference'),('reference','reference')]
        return res

    name = fields.Char('Field Name', required=True, default='x_', index=True)
    field_description = fields.Char('Field Label')
    model_id = fields.Many2one('ir.model', 'Model', required=True, index=True, ondelete='cascade')
    ttype = fields.Selection(_get_fields_type, 'Field Type', required=True)
    help = fields.Text(string='Field Help', translate=True)
    required = fields.Boolean(string='Required')
    readonly = fields.Boolean(string='Readonly')
    copied = fields.Boolean(string='Copied')
    groups = fields.Many2many('res.groups', 'custom_fields_group_rel', 'field_ids', 'group_id')

    on_delete = fields.Selection([('cascade', 'Cascade'), ('set null', 'Set NULL'), ('restrict', 'Restrict')],
                                 string='On Delete', default='set null', help='On delete property for many2one fields')
    state = fields.Char('State')
    selection_ids = fields.One2many("ir.model.fields.selection.custom", "custom_fields_id",
                                    string="Selection Options", copy=True)
    relation = fields.Char(string="Relation")
    relation_field = fields.Char(string="Relation Field")
    where_to_add = fields.Selection([('after', 'After'), ('before', 'Before')], string="Where to Add")
    after_which_field = fields.Many2one('ir.model.fields', string="After which Field")
    domain = fields.Text(default='[]')
    tab_list = fields.Many2one('ir.model.tabs', domain="[('model_id.id', '=',model_id)]", string="Tab List")
    view_id = fields.Many2one('ir.ui.view', string="View")
    domain_list = fields.Char(string="Based on Field", help="Coupon program will work for selected customers only")
    model_field = fields.Char('model Field', related='relation')

    @api.onchange('tab_list')
    def change_field_vals(self):
        if self.tab_list:
            self.update({'after_which_field': False})

    @api.onchange('after_which_field')
    def change_tab_vals(self):
        if self.after_which_field:
            self.update({'tab_list': False})

    @api.onchange('model_id')
    def field_domain(self):
        if self.model_id:
            model_name = self.model_id.model

            if model_name == 'product.template':
                view_id = self.env.ref('product.product_template_only_form_view')
            else:
                view_id = self.env['ir.ui.view'].sudo().search(
                    [('model', '=', model_name), ('type', '=', 'form'), ('active', '=', True),
                     ('inherit_id', '=', False)], limit=1)

            if view_id:
                fields = []
                view_architecture = str(view_id.arch_base)
                document = ET.fromstring(view_architecture)
                for tag in document.findall('.//field'):
                    fields.append(tag.attrib['name'])

                return {
                    'domain': {'after_which_field': [('name', 'in', fields), ('model_id.id', '=', self.model_id.id)]}}

    def update_field(self):
        context = self._context.copy()

        context.update({'default_name': self.name,
                        'default_field_description': self.field_description,
                        'default_model_id': self.model_id.id,
                        'default_ttype': self.ttype,
                        'default_relation': self.relation,
                        'default_required': self.required,
                        'default_after_which_field': self.after_which_field.id,
                        'default_where_to_add': self.where_to_add,
                        'default_groups': self.view_id.groups_id.ids,
                        'default_help': self.help,
                        'default_readonly': self.readonly,
                        'default_selection_ids': self.selection_ids.ids,
                        'default_copied': self.copied,
                        'default_view_id': self.view_id.id,
                        'default_tab_list': self.tab_list.id,
                        'domain_list': self.domain_list,
                        'default_model_field': self.model_field,
                        })
        view_id = self.env.ref('bi_global_custom_fields.global_custom_fields_update_view').id
        if self.model_id:
            model_name = self.model_id.model

            if model_name == 'product.template':
                custom_view_id = self.env.ref('product.product_template_only_form_view')

            if model_name == 'res.users':
                custom_view_id = self.env['ir.ui.view'].sudo().search([('name', '=', 'res.users.form')])

            else:
                custom_view_id = self.env['ir.ui.view'].sudo().search(
                    [('model', '=', model_name), ('type', '=', 'form'), ('active', '=', True),
                     ('inherit_id', '=', False)], limit=1)

            if custom_view_id:
                fields = []
                view_architecture = str(custom_view_id.arch_base)
                document = ET.fromstring(view_architecture)
                for tag in document.findall('.//field'):
                    fields.append(tag.attrib['name'])
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.fields',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': context,
            # 'domain': {'default_after_which_field': [(4, x, None) for x in fields]}
        }

    def write_fields(self):

        view_arch = str(self.view_id.arch_base)
        doc = ET.fromstring(view_arch)
        custom_field_string = ""
        if self.tab_list and not self.after_which_field:
            view_arch = str(self.view_id.arch_base)
            doc = ET.fromstring(view_arch)
            count = 1
            for tag in doc.findall('.//page'):
                if not self.tab_list.tab_name:
                    if tag.attrib.get('string') == self.tab_list.tab_string:
                        custom_field_string = ""
                        custom_field_string += "<?xml version='1.0'?>\n"
                        custom_field_string += "   <data>\n"
                        custom_field_string += "      <xpath expr=\"//notebook/page[" + str(
                            count) + "]\" position=\"inside\">\n"
                        custom_field_string += "      <group>\n"
                        custom_field_string += "      	<group>\n"
                        custom_field_string += "        	<field string= \"" + self.field_description + "\" name=\"" + self.name + "\" ttype=\"" + self.ttype + "\"/>\n"
                        custom_field_string += "      	</group>\n"
                        custom_field_string += "      </group>\n"
                        custom_field_string += "     </xpath>\n"
                        custom_field_string += "   </data>\n"
                    count += 1
            if self.tab_list.tab_name:
                custom_field_string = ""
                custom_field_string += "<?xml version='1.0'?>\n"
                custom_field_string += "   <data>\n"
                custom_field_string += "      <page name= \"" + self.tab_list.tab_name + "\" position=\"inside\">\n"
                custom_field_string += "      <group>\n"
                custom_field_string += "      	<group>\n"
                custom_field_string += "   		<field string= \"" + self.field_description + "\" name=\"" + self.name + "\" ttype=\"" + self.ttype + "\"/>\n"
                custom_field_string += "      	</group>\n"
                custom_field_string += "      </group>\n"
                custom_field_string += "   	 </page>\n"
                custom_field_string += "   </data>"


        elif self.after_which_field and self.where_to_add:
            custom_field_string = ""
            custom_field_string += "<?xml version='1.0'?>\n"
            custom_field_string += "   <data>\n"
            custom_field_string += "   	<field name=\"" + self.after_which_field.name + "\" position=\"" + self.where_to_add + "\">\n"
            custom_field_string += "   		<field string= \"" + self.field_description + "\" name=\"" + self.name + "\" ttype=\"" + self.ttype + "\"/>\n"
            custom_field_string += "    </field>\n"
            custom_field_string += "   </data>\n"
        else:
            raise Warning("Please add either After which field or tab to update field")

        model_field = self.env['ir.model.fields'].search([('name', '=', self.name), ('state', '=', 'manual'),
                                                          ('model_id', '=', self.model_id.id)])
        selection_to_remove = self.env['ir.model.fields.selection'].sudo().search(
            [('field_id', '=', model_field.id)])

        for record in selection_to_remove:
            record.unlink()

        selection_model = self.env['ir.model.fields.selection']
        if self.selection_ids:
            for rec in self.selection_ids:
                selection = selection_model.sudo().create(
                    {'field_id': model_field.id, 'name': rec.name, 'value': rec.value})
        model_field.sudo().update({
            'field_description': self.field_description,
            'relation': self.relation,
            'required': self.required,
            'help': self.help,
            'readonly': self.readonly,
            'copied': self.copied,
            'domain': self.domain_list,

        })
        field = self.search([('name', '=', self.name),('model_id', '=', self.model_id.id)], limit=1)
        field.update({
            'field_description': self.field_description,
            'relation': self.relation,
            'required': self.required,
            'help': self.help,
            'readonly': self.readonly,
            'copied': self.copied,
            'selection_ids': self.selection_ids.ids,
        })

        field.with_context(flag=True).unlink()
        self.view_id.with_context(from_bi=True).update({
            'arch_base': custom_field_string,
            'groups_id': [(6, 0, self.groups.ids)], })

    def unlink(self):
        for rec in self:
            if not self._context.get('flag'):
                rec.view_id.unlink()
                required_field = self.env['ir.model.fields'].search([('name', '=', rec.name), ('state', '=', 'manual')])
                required_field.unlink()

        return super(CustomFields, self).unlink()
