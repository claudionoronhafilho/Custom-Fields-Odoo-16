# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from subprocess import call
from lxml import etree
from xml.dom import minidom
import xml.etree.ElementTree as xee
import types
import re
from odoo import fields, models, api, tools, _
from odoo.exceptions import Warning, UserError, ValidationError

class IrModelTabs(models.Model):
	_name = "ir.model.tabs"
	_description = "Ir Model Tabs"
	_rec_name = 'tab_string'

	tab_string = fields.Char(string="String")
	tab_name = fields.Char(string="Name")
	model_id = fields.Many2one('ir.model')
	position = fields.Integer(string="Position")
	view_id = fields.Many2one('ir.ui.view',string="Created view")

class IrModelFieldInherit(models.Model):
	_inherit = 'ir.model.fields'
	_description = "Ir Model Field Inherit"

	view_id = fields.Many2one('ir.ui.view')	


