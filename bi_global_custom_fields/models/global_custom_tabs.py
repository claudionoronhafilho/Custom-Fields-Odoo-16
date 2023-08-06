# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from subprocess import call
from lxml import etree
from xml.dom import minidom
import types
import xml.etree.ElementTree as ET
from odoo import fields, models, api, tools, _
from odoo.exceptions import Warning, UserError, ValidationError


class IrGlobalCustomTabs(models.Model):
    _name = 'ir.global.tabs'
    _description = "Custom Global Tabs"

    name = fields.Char('Name', required=True)
    field_description = fields.Char('Tabs Label', required=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, index=True, ondelete='cascade')
    groups = fields.Many2many('res.groups', 'ir_models_tabs_group_rel', 'field_id', 'group_id')
    tab_list = fields.Many2one('ir.model.tabs', string="Tab List")
    where_to_add = fields.Selection([('after', 'After'), ('before', 'Before')], string="Where to Add")
    view_id = fields.Many2one('ir.ui.view', string="View")

    @api.model
    def default_get(self, fields):
        res = super(IrGlobalCustomTabs, self).default_get(fields)
        all_models = self.env['ir.model'].search([])
        for model in all_models:
            model_name = model.model
            if model_name == 'product.template':
                view_id = self.env.ref('product.product_template_only_form_view')
            if model_name == 'product.product':
                view_id = self.env.ref('product.product_normal_form_view')
            if model_name == 'res.users':
                view_id = self.env['ir.ui.view'].sudo().search([('name', '=', 'res.users.form')])
            else:
                view_id = self.env['ir.ui.view'].sudo().search(
                    [('model', '=', model_name), ('type', '=', 'form'), ('active', '=', True),
                     ('inherit_id', '=', False)], limit=1)
            if view_id:
                view_architecture = str(view_id.arch_base)
                document = ET.fromstring(view_architecture)
                pos = 1
                for tag in document.findall('.//page'):
                    if tag.attrib.get('string'):
                        tab = self.env['ir.model.tabs'].sudo().search(
                            [('tab_string', '=', tag.attrib['string']), ('model_id', '=', model.id)])
                        if tag.attrib.get('name'):
                            tab.write({'tab_name': tag.attrib.get('name')})
                    if tab:
                        pass
                    else:
                        if tag.attrib.get('string'):
                            string = tag.attrib['string']
                            self.env['ir.model.tabs'].sudo().create(
                                {'tab_string': string, 'model_id': model.id, 'position': pos})
                            pos += 1
        return res

    def create_global_custome_tabs(self):

        model_id = self.env['ir.model'].sudo().search([('model', '=', self.model_id.model)], limit=1).model
        if model_id == 'res.users':
            view_id = self.env['ir.ui.view'].sudo().search([('name', '=', 'res.users.form')])
        else:
            view_id = self.env['ir.ui.view'].sudo().search(
                [('model', '=', model_id), ('type', '=', 'form'), ('active', '=', True), ('inherit_id', '=', False)],
                limit=1)
        if model_id == 'product.template':
            view_id = self.env.ref('product.product_template_only_form_view')
        if model_id == 'product.product':
            view_id = self.env['ir.ui.view'].sudo().search(
                [('xml_id', '=', 'product.product_normal_form_view'), ('name', '=', 'product.product.form')])

        inherit_id = self.env.ref(view_id.xml_id)

        if self.tab_list and self.where_to_add:
            view_arch = str(view_id.arch_base)
            doc = ET.fromstring(view_arch)
            count = 1
            for tag in doc.findall('.//page'):
                if not self.tab_list.tab_name:
                    if tag.attrib.get('string') == self.tab_list.tab_string:
                        custom_tab_string = ""
                        custom_tab_string += "<?xml version='1.0'?>\n"
                        custom_tab_string += "   <data>\n"
                        custom_tab_string += "      <xpath expr=\"//notebook/page[" + str(
                            count) + "]\" position=\"" + self.where_to_add + "\">\n"
                        custom_tab_string += "   		<page string= \"" + self.field_description + "\" name= \"" + self.name + "\"/>\n"
                        custom_tab_string += "   	 </xpath>\n"
                        custom_tab_string += "   </data>"

                    count += 1
                elif self.tab_list.tab_name:
                    custom_tab_string = ""
                    custom_tab_string += "<?xml version='1.0'?>\n"
                    custom_tab_string += "   <data>\n"
                    custom_tab_string += "      <page name= \"" + self.tab_list.tab_name + "\" position=\"" + self.where_to_add + "\">\n"
                    custom_tab_string += "   		<page string= \"" + self.field_description + "\" name= \"" + self.name + "\"/>\n"
                    custom_tab_string += "   	 </page>\n"
                    custom_tab_string += "   </data>"

        else:

            custom_tab_string = ""
            custom_tab_string += "<?xml version='1.0'?>\n"
            custom_tab_string += "   <data>\n"
            custom_tab_string += "      <xpath expr=\"//notebook\" position=\"inside\">\n"
            custom_tab_string += "   		<page string= \"" + self.field_description + "\" name= \"" + self.name + "\"/>\n"
            custom_tab_string += "   	 </xpath>\n"
            custom_tab_string += "   </data>"
        if custom_tab_string:
            generated_view = self.env['ir.ui.view'].with_context(from_bi=True).sudo().create({'name': 'global.custom.tabs',
                                                                   'type': 'form',
                                                                   'model': model_id,
                                                                   'mode': 'extension',
                                                                   'inherit_id': inherit_id.id,
                                                                   'arch_base': custom_tab_string,
                                                                   'active': True,
                                                                   'groups_id': [(6, 0, self.groups.ids)],
                                                                   })
            tab = self.env['ir.model.tabs'].sudo().create(
                {'model_id': self.model_id.id, 'tab_string': self.field_description, 'tab_name': self.name,
                 'view_id': generated_view.id})

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def update_tab(self):
        context = self._context.copy()
        tab_to_update = self.env['ir.model.tabs'].sudo().search(
            [('tab_name', '=', self.name), ('model_id', '=', self.model_id.id)])
        context.update(
            {'default_name': self.name, 'default_model_id': self.model_id.id, 'default_tab_list': self.tab_list.id,
             'default_field_description': self.field_description, 'default_view_id': tab_to_update.view_id.id,
             'default_groups': tab_to_update.view_id.groups_id.ids})
        view_id = self.env.ref('bi_global_custom_fields.global_custom_tabs_update_view').id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.global.tabs',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': context,
        }

    def update_current_tab(self):
        location = None
        position = None
        location1 = None
        position1 = None
        view_arch = str(self.view_id.arch_base)
        doc = ET.fromstring(view_arch)
        for tag in doc.findall(".//xpath"):
            if tag.attrib.get('expr') and tag.attrib.get('position'):
                location = tag.attrib['expr']
                position = tag.attrib['position']
        for tag in doc.findall(".//page"):
            if tag.attrib.get('name') and tag.attrib.get('position'):
                location1 = tag.attrib['name']
                position1 = tag.attrib['position']

        if location and position:
            custom_tab_string = ""
            custom_tab_string += "<?xml version='1.0'?>\n"
            custom_tab_string += "   <data>\n"
            custom_tab_string += "      <xpath expr=\"" + location + "\" position=\"" + position + "\">\n"
            custom_tab_string += "   		<page string= \"" + self.field_description + "\" name= \"" + self.name + "\"/>\n"
            custom_tab_string += "   	 </xpath>\n"
            custom_tab_string += "   </data>"
        if location1 and position1:
            custom_tab_string = ""
            custom_tab_string += "<?xml version='1.0'?>\n"
            custom_tab_string += "   <data>\n"
            custom_tab_string += "      <page name= \"" + location1 + "\" position=\"" + position1 + "\">\n"
            custom_tab_string += "   		<page string= \"" + self.field_description + "\" name= \"" + self.name + "\"/>\n"
            custom_tab_string += "   	 </page>\n"
            custom_tab_string += "   </data>"
        model_tab = self.env['ir.model.tabs'].sudo().search([('tab_name', '=', self.name), ('model_id', '=', self.model_id.id)])
        model_tab.sudo().update({'tab_string': self.field_description})
        self.view_id.with_context(from_bi=True).sudo().update({
            'arch_base': custom_tab_string,
            'groups_id': [(6, 0, self.groups.ids)],
        })

        tab_required = self.search([('name', '=', self.name), ('model_id', '=', self.model_id.id)])
        tab_required.update({'field_description': self.field_description})
        self.with_context(flag=True).unlink()

    def unlink(self):
        for tab in self:
            if not self._context.get('flag'):
                model_tab = self.env['ir.model.tabs'].sudo().search([('model_id', '=', tab.model_id.id)],limit=1)
                required_tab_view = self.env['ir.model.tabs'].sudo().search([('tab_name', '=', tab.name)])
                
                custom_field = self.env['custom.fields'].sudo().search([('tab_list', '=', required_tab_view.id)])
                for fields in custom_field:
                    fields.unlink()
                required_tab_view.view_id.unlink()

                required_tab_view.unlink()

        return super(IrGlobalCustomTabs, self).unlink()
