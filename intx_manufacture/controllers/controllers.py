# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from datetime import datetime

class IntxManufacture(http.Controller):
    @http.route('/intx_manufacture/test',  auth='public', type='http', methods=['POST'], csrf=False)
    def index(self, **kw):
        
        return http.Response(
            json.dumps({
                "result": True
            }),
            content_type='application/json'
        )

    @http.route('/intx_manufacture/login/check', auth='public', type='http', methods=['POST'], csrf=False)
    def login_check(self, **kwargs):

        data = json.loads(request.httprequest.data)

        request_list = data.get("request", [])

        user_data = request_list[0]
        login = user_data.get("user_login")
        password = user_data.get("password")
        devid = user_data.get("devid")

        user = request.env['res.users'].sudo().search([
            ('login', '=', login)
        ], limit=1)

        print("email : ",user.login)
        print("User  : ",user.name)
        print("login : ",user.id)
        print("PassIn: ",repr(password))

        credential = {
            'type': 'password',
            'password': password
        }

        try:
            user.with_user(user)._check_credentials(credential, request.env)
            print("Password benar")
            Result =  True
            User_id = user.id
            User_Name = user.name
            User_login = user.login
        except Exception:
            print("Password salah")
            Result = False
            User_id = 0
            User_Name = ""
            User_login = ""

        return http.Response(
            json.dumps({
                "result": Result,
                "user_id": User_id,
                "user_name": User_Name,
                "user_login" : User_login,
            }),
            content_type='application/json'
        )
     
    @http.route('/intx_manufacture/production/status', auth='public', type='http', methods=['POST'], csrf=False)
    def production_status(self, **kwargs):

        data = json.loads(request.httprequest.data)
        request_list = data.get("request", [])

        request_data = request_list[0]
        input_date = request_data.get("date")
        status ="No Work"
        domain = []

        if input_date:
            dt = datetime.strptime(input_date, "%Y%m%d")
            date_from = dt.strftime("%Y-%m-%d 00:00:00")
            date_to = dt.strftime("%Y-%m-%d 23:59:59")

            domain.append(('date_start', '>=', date_from))
            domain.append(('date_start', '<=', date_to))

        domain.append(('state', 'in', ['ready', 'progress']))
        
        workcenters = request.env['mrp.workcenter'].sudo().search([])

        response = []

        for wc in workcenters:

            wo_domain = domain + [('workcenter_id', '=', wc.id)]

            workorder = request.env['mrp.workorder'].sudo().search(
                wo_domain,
                limit=1,
                order="date_start desc"
            )

            if workorder:

                mo = workorder.production_id
                
                finished_move = mo.move_finished_ids.filtered(
                    lambda m: m.product_id == mo.product_id
                )[:1]

                status = mo.state
                
                reqty = 0

                if finished_move:
                    reqty = sum(
                        finished_move.move_line_ids.mapped('quantity')
                    )

                plqty = mo.product_qty

                wo_data = {
                    "workorder_id": workorder.id,
                    "workorder_name": workorder.name,
                    "mo_name": mo.name,
                    "product": workorder.product_id.name,
                    "qty_production": workorder.qty_production,
                    "qty_produced": workorder.qty_produced,
                    "state": workorder.state
                }
             

            else:
                wo_data = None
                reqty = 0
                plqty = 0

            response.append({
                "workcenter_id": wc.id,
                "workcenter_name": wc.name,
                "manufacture_order": wo_data,
                "qty_produced": reqty,
                "product_qty": plqty,
                "status": status
            })

        return http.Response(
            json.dumps({
                "result": True,
                "response": response
            }),
            content_type='application/json'
        )
    
    @http.route('/intx_manufacture/production/workorder', auth='public', type='http', methods=['POST'], csrf=False)
    def load_workorder(self, **kwargs):

        data = json.loads(request.httprequest.data)

        request_list = data.get("request", [])

        request_data = request_list[0]
        date = request_data.get("date")
        workcenter_id = request_data.get("workcenter_id")
        domain = []
        
        if date:
            dt = datetime.strptime(date, "%Y%m%d")
            date_from = dt.strftime("%Y-%m-%d 00:00:00")
            date_to = dt.strftime("%Y-%m-%d 23:59:59")

            domain.append(('date_start', '>=', date_from))
            domain.append(('date_start', '<=', date_to))
            domain.append(('workorder_ids.workcenter_id', '=', int(workcenter_id)))

        productions = request.env['mrp.production'].sudo().search(domain)
    
        response = []

        shift =0

        for mo in productions:
            
            product = mo.product_id
            workorder = mo.workorder_ids[:1]

            workcenter_val = None

            if workorder:
                workcenter_val = workorder.workcenter_id.id
                workcenter_name = workorder.workcenter_id.name

            response.append({
                    "workcenter_id": workcenter_val,
                    "workcenter_name": workcenter_name,
                    "manufacture_order": mo.name,
                    "workorder_id": mo.id,
                    "default_code": product.default_code or "",
                    "product_name": product.name,
                    "product_qty": mo.product_qty,                   
                    "qty_produced": mo.qty_produced,
                    "balance": mo.qty_produced-mo.product_qty,
                    "rate": (mo.qty_produced/mo.product_qty)*100,
                    "status": mo.state
            })    

        return http.Response(
            json.dumps({
                "result": True,
                "response": response
            }),
            content_type='application/json'
        )
    
    @http.route('/intx_manufacture/production/workorder/realtime', auth='public', type='http', methods=['POST'], csrf=False)
    def load_workscreen_realtime(self, **kwargs):

        data = json.loads(request.httprequest.data)
        request_list = data.get("request", [])

        if not request_list:
            return http.Response(json.dumps({"success": False}), content_type='application/json')

        request_data = request_list[0]

        domain = []

        workcenter_id = request_data.get("workcenter_id")
        if workcenter_id:
            domain.append(('workorder_ids.workcenter_id', '=', int(workcenter_id)))
            domain.append(('workorder_ids.state', 'in', ['ready', 'progress']))

        productions = request.env['mrp.production'].sudo().search(domain)

        response = []

        for mo in productions:

            product = mo.product_id

            workorder = mo.workorder_ids.filtered(
                lambda w: w.workcenter_id.id == int(workcenter_id)
            )[:1]

            workcenter_name = workorder.workcenter_id.name

            finished_move = mo.move_finished_ids.filtered(
                lambda m: m.product_id == product
            )[:1]

            produced_qty = sum(finished_move.move_line_ids.mapped('quantity')) if finished_move else 0

            balance = mo.product_qty - produced_qty
            rate = (produced_qty / mo.product_qty * 100) if mo.product_qty else 0

            if mo.state == "progress":
                response.append({
                    "workcenter_id": workorder.workcenter_id.id if workorder else None,
                    "workcenter_name": workcenter_name,
                    "manufacture_order": mo.name,
                    "wo_id": mo.id,
                    "default_code": product.default_code or "",
                    "product_name": product.name,                   
                    "product_qty": mo.product_qty,
                    "qty_produced": produced_qty,                    
                    "balance": balance,
                    "rate": rate,
                    "status": mo.state
                })

        return http.Response(
            json.dumps({
                "success": True,
                "response": response
            }),
            content_type='application/json'
        )
    
    @http.route('/intx_manufacture/production/workorder/update/status', auth='public', type='http', methods=['POST'], csrf=False)
    def update_status(self, **kwargs):

        data = json.loads(request.httprequest.data)

        request_list = data.get("request", [])

        user_data = request_list[0]
        workorder_id = user_data.get("workorder_id")
        state = user_data.get("state")

        workorders = request.env['mrp.workorder'].sudo().search([
            ('production_id', '=', workorder_id)
        ], limit=1)

        result = False
        message = ""

        if workorders.state == "done":
            message = "Work Order Done"

        elif workorders.state == "cancel":
            message = "Work Order Cancelled"

        if state == "RUN":
            if workorders.state in ["ready", "pending"]:
                workorders.button_start()
                result = True
                message = "Work Order Start"

                moves = workorders.move_finished_ids | workorders.move_raw_ids

                for move in moves:
                    move.move_line_ids.unlink()

        elif state == "PAUSE":
            if workorders.state == "progress":
                workorders.button_pending()
                result = True
                message = "Pause Triggered"
       
        return http.Response(
            json.dumps({
                "result": result,
                "message": message
            }),
            content_type='application/json'
        )
    
    @http.route('/intx_manufacture/production/workorder/update/qty', auth='public', type='http', methods=['POST'], csrf=False)
    def update_qty(self, **kwargs):

        data = json.loads(request.httprequest.data)

        request_list = data.get("request", [])

        user_data = request_list[0]
        workorder_id = user_data.get("workorder_id")
        qty = user_data.get("qty")
        LotNumber = user_data.get("LotNumber")

        workorders = request.env['mrp.workorder'].sudo().search([
            ('production_id', '=', workorder_id)
        ], limit=1)

        status = workorders.state
        print(status)

        response = []
        result = False
        message = ""

        tracking = workorders.product_id.tracking
        print(tracking)

        if status == "progress":
            if tracking == "none" :
                message = "tanpa tracking"
                result = True

                # Ambil finished move utama
                finished_move = workorders.move_finished_ids.filtered(
                    lambda m: m.product_id == workorders.product_id
                )[:1]

                if not finished_move:
                    return http.Response(
                        json.dumps({"success": False, "message": "Finished move tidak ditemukan"}),
                        content_type='application/json'
                    )

                finished_move = finished_move[0]

                move_line = request.env['stock.move.line'].sudo().search([
                    ('move_id', '=', finished_move.id)
                ], limit=1)

                target_qty = finished_move.product_uom_qty

                # Clamp supaya tidak melebihi target
                if qty > target_qty:
                    qty = target_qty

                if move_line:
                    # 🔥 REPLACE nilai lama
                    move_line.quantity = qty
                else:
                    request.env['stock.move.line'].sudo().create({
                        'move_id': finished_move.id,
                        'product_id': finished_move.product_id.id,
                        'product_uom_id': finished_move.product_uom.id,
                        'quantity': qty,
                        'location_id': finished_move.location_id.id,
                        'location_dest_id': finished_move.location_dest_id.id,
                    })

                production = workorders.production_id
                production.qty_producing = qty

                response.append({
                    "rtnval": True,
                    "message": "Replace Qty",
                    "qty_done": qty
                })

            elif tracking == "lot":

                message = "tracking Lot"
                result = True

                # proteksi state workorder
                if workorders.state in ['done', 'cancel']:
                    return http.Response(
                        json.dumps({
                            "rtnval": False,
                            "message": "Workorder sudah selesai / cancel"
                        }),
                        content_type='application/json'
                    )

                Lot = request.env['stock.lot'].sudo()

                # cari lot
                lot = Lot.search([
                    ('name', '=', LotNumber),
                    ('product_id', '=', workorders.product_id.id)
                ], limit=1)

                # create lot jika belum ada
                if not lot:
                    lot = Lot.create({
                        'name': LotNumber,
                        'product_id': workorders.product_id.id
                    })

                # ambil finished move
                finished_move = workorders.move_finished_ids.filtered(
                    lambda m: m.product_id.id == workorders.product_id.id
                )

                if not finished_move:
                    return http.Response(
                        json.dumps({
                            "rtnval": False,
                            "message": "Finished move tidak ditemukan"
                        }),
                        content_type='application/json'
                    )

                finished_move = finished_move[0]

                target_qty = finished_move.product_uom_qty

                MoveLine = request.env['stock.move.line'].sudo()

                # cari move line berdasarkan lot
                move_line = MoveLine.search([
                    ('move_id', '=', finished_move.id),
                    ('lot_id', '=', lot.id)
                ], limit=1)

                if move_line:
                    move_line.quantity = qty
                else:
                    MoveLine.create({
                        'move_id': finished_move.id,
                        'product_id': finished_move.product_id.id,
                        'product_uom_id': finished_move.product_uom.id,
                        'quantity': qty,
                        'lot_id': lot.id,
                        'location_id': finished_move.location_id.id,
                        'location_dest_id': finished_move.location_dest_id.id,
                    })

                # hitung total qty dari semua lot
                total_qty = sum(
                    finished_move.move_line_ids.mapped('quantity')
                )

                # clamp agar tidak melebihi target
                if total_qty > target_qty:
                    total_qty = target_qty

                # update qty producing workorder
                workorders.qty_producing = total_qty

                response.append({
                    "rtnval": True,
                    "message": "Lot processed",
                    "lot": lot.name,
                    "quantity": qty,
                    "total_producing": total_qty
                })

            elif tracking == "serial" :
                message = "tracking Serial"

                result = True

                lot = request.env['stock.lot'].sudo().search([
                    ('name', '=', LotNumber),
                    ('product_id', '=', workorders.product_id.id)
                ], limit=1)

                if not lot:
                    lot = request.env['stock.lot'].sudo().create({
                        'name': LotNumber,
                        'product_id': workorders.product_id.id
                    })

                finished_move = workorders.move_finished_ids.filtered(
                    lambda m: m.product_id == workorders.product_id
                )[:1]

                finished_move = finished_move[0]

                request.env['stock.move.line'].sudo().create({
                    'move_id': finished_move.id,
                    'product_id': finished_move.product_id.id,
                    'product_uom_id': finished_move.product_uom.id,
                    'quantity': 1,
                    'lot_id': lot.id,
                    'location_id': finished_move.location_id.id,
                    'location_dest_id': finished_move.location_dest_id.id,
                })

                response.append({
                    "rtnval": True,
                    "message": "Serial processed",
                    "serial": lot.name
                })

        message = "Work Order tidak Running"
         
        return http.Response(
            json.dumps({
                "result": result,
                "message": message,
                "response" : response
            }),
            content_type='application/json'
        )

    @http.route('/intx_manufacture/production/workorder/update/close', auth='public', type='http', methods=['POST'], csrf=False)
    def update_close(self, **kwargs):

        data = json.loads(request.httprequest.data)

        request_list = data.get("request", [])

        user_data = request_list[0]
        workorder_id = user_data.get("workorder_id")

        result = False
        message = "work Order tidak sedang progress tidak bisa di close"

        workorders = request.env['mrp.workorder'].sudo().search([
            ('production_id', '=', workorder_id)
        ], limit=1)

        if workorders.state == "progress":
            workorders.button_finish()
            result = True
            message = "to Close Called"


        return http.Response(
            json.dumps({
                "result": result,
                "message": message
            }),
            content_type='application/json'
        )
    
    @http.route('/intx_manufacture/production/workorder/update/done', auth='public', type='http', methods=['POST'], csrf=False)
    def update_done(self, **kwargs):

        result = False
        message = ""
        response  = []
        data = json.loads(request.httprequest.data)

        request_list = data.get("request", [])

        user_data = request_list[0]
        workorder_id = user_data.get("workorder_id")

        workorders = request.env['mrp.workorder'].sudo().search([
            ('production_id', '=', workorder_id)
        ], limit=1)

        tracking = workorders.product_id.tracking
        print(tracking)

        if tracking=="none" :
            message = "DONE tanpa fitur Tracking"
            # Ambil finished move utama
            finished_move = workorders.move_finished_ids.filtered(
                lambda m: m.product_id == workorders.product_id
            )[:1]

            if not finished_move:
                return http.Response(
                    json.dumps({"success": False, "message": "Finished move tidak ditemukan"}),
                    content_type='application/json'
                )

            finished_move = finished_move[0]

            move_line = request.env['stock.move.line'].sudo().search([
                ('move_id', '=', finished_move.id)
            ], limit=1)

            mo = workorders.production_id
            target = mo.product_qty
            current = mo.qty_produced

            finished_move = workorders.move_finished_ids.filtered(
                lambda m: m.product_id == workorders.product_id
            )[:1]

            total_qty = sum(finished_move.move_line_ids.mapped('quantity'))

            qty = total_qty
            final_qty = current + qty

            print("Target :",target," current:",current," Qty : ",qty)

            # tentukan qty produksi
            if final_qty >= target:
                produce_qty = target - current
                msg = "MO Finished Complete"
            else:
                produce_qty = qty
                msg = "MO Finished UnComplete"

            # set qty producing
            mo.write({
                "qty_producing": produce_qty
            })

            # ambil finished move
            finished_move = mo.move_finished_ids.filtered(
                lambda m: m.product_id == mo.product_id
            )[:1]

            if finished_move:

                move_line = finished_move.move_line_ids[:1]

                if move_line:
                    move_line.quantity = current + produce_qty
                else:
                    request.env['stock.move.line'].sudo().create({
                        'move_id': finished_move.id,
                        'product_id': finished_move.product_id.id,
                        'product_uom_id': finished_move.product_uom.id,
                        'quantity': current + produce_qty,
                        'location_id': finished_move.location_id.id,
                        'location_dest_id': finished_move.location_dest_id.id,
                    })

            # refresh record supaya qty_produced terupdate
            mo.invalidate_recordset()

            # finish semua workorder
            for wo in mo.workorder_ids:
                if wo.state != 'done':
                    wo.button_finish()

            # mark MO selesai
            if qty >= mo.product_qty:
                mo.button_mark_done()
            else:
                # adjust raw material
                for move in mo.move_raw_ids:

                    required_qty = (move.product_uom_qty / mo.product_qty) * qty

                    move_line = move.move_line_ids[:1]

                    if move_line:
                        move_line.quantity = required_qty

                mo.with_context(skip_backorder=True).button_mark_done()

            response.append({
                "rtnval": True,
                "message": msg,
                "qty_produced": qty
            })

        elif tracking=="lot":
            message = "DONE fitur Tracking LOT"

            mo = workorders.production_id
            target = mo.product_qty
            current = mo.qty_produced

            finished_move = workorders.move_finished_ids.filtered(
                lambda m: m.product_id == workorders.product_id
            )[:1]

            total_qty = sum(finished_move.move_line_ids.mapped('quantity'))

            qty = total_qty
            final_qty = current + qty

            print("Target :",target," current:",current," Qty : ",qty)

            # tentukan qty produksi
            if final_qty >= target:
                produce_qty = target - current
                msg = "MO Finished Complete"
                mo.button_mark_done()

            else:
                produce_qty = qty
                msg = "MO Finished UnComplete"
                mo.with_context(skip_backorder=True).button_mark_done()

            response.append({
                "rtnval": True,
                "message": msg,
                "qty_produced": qty
            })

        elif tracking=="serial" :
            message = "DONE fitur Tracking SERIAL"

            mo = workorders.production_id
            target = mo.product_qty
            current = mo.qty_produced

            finished_move = workorders.move_finished_ids.filtered(
                lambda m: m.product_id == workorders.product_id
            )[:1]

            total_qty = sum(finished_move.move_line_ids.mapped('quantity'))

            qty = total_qty
            final_qty = current + qty

            print("Target :",target," current:",current," Qty : ",qty)

            # tentukan qty produksi
            if final_qty >= target:
                produce_qty = target - current
                msg = "MO Finished Complete"
                mo.button_mark_done()

            else:
                produce_qty = qty
                msg = "MO Finished UnComplete"
                mo.with_context(skip_backorder=True).button_mark_done()

            response.append({
                "rtnval": True,
                "message": msg,
                "qty_produced": qty
            })
                
        return http.Response(
            json.dumps({
                "result": result,
                "message": message,
                "response": response
            }),
            content_type='application/json'
        )