"""AGP — Sistema de Gestión de Préstamos — Flask web app."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date

# En bundle PyInstaller los recursos están en sys._MEIPASS;
# en desarrollo están junto al propio archivo.
if getattr(sys, "frozen", False):
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(_BASE, "templates"),
    static_folder=os.path.join(_BASE, "static"),
)
app.secret_key = "agp-secret-2026"

# ── Filtros Jinja2 ────────────────────────────────────────────────────────────

@app.template_filter("moneda")
def fmt_moneda(v, simbolo="RD$"):
    try:
        return f"{simbolo} {float(v):,.2f}"
    except (TypeError, ValueError):
        return f"{simbolo} 0.00"

@app.template_filter("estado_color")
def estado_color(e):
    return {
        "ACTIVO":       "text-blue-600",
        "AL_DIA":       "text-green-600",
        "VENCIDO":      "text-red-600",
        "CANCELADO":    "text-slate-400",
        "REFINANCIADO": "text-amber-600",
    }.get(e, "text-slate-600")

@app.template_filter("estado_bg")
def estado_bg(e):
    return {
        "ACTIVO":       "bg-blue-100 text-blue-700",
        "AL_DIA":       "bg-green-100 text-green-700",
        "VENCIDO":      "bg-red-100 text-red-700",
        "CANCELADO":    "bg-slate-100 text-slate-600",
        "REFINANCIADO": "bg-amber-100 text-amber-700",
    }.get(e, "bg-slate-100 text-slate-600")

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    from controllers.reporte_controller import dashboard as get_dash
    datos = get_dash()
    return render_template("dashboard.html", datos=datos, hoy=date.today(),
                           active_section="dashboard")

# ── Clientes ──────────────────────────────────────────────────────────────────

@app.route("/clientes")
def clientes_lista():
    q = request.args.get("q", "").strip()
    from controllers.cliente_controller import buscar, todos
    rows = buscar(q) if q else todos()
    return render_template("clientes/lista.html", clientes=rows, q=q,
                           active_section="clientes")

@app.route("/clientes/nuevo", methods=["GET", "POST"])
def cliente_nuevo():
    from config import TIPOS_DOC, CALIFICACIONES, TIPOS_TASA
    if request.method == "POST":
        datos = request.form.to_dict()
        try:
            from controllers.cliente_controller import guardar_cliente
            guardar_cliente(datos)
            flash("Cliente creado correctamente.", "success")
            return redirect(url_for("clientes_lista"))
        except Exception as e:
            return render_template("clientes/form.html", datos=datos, error=str(e),
                                   tipos_doc=TIPOS_DOC, calificaciones=CALIFICACIONES,
                                   tipos_tasa=TIPOS_TASA, modo="nuevo",
                                   active_section="clientes")
    return render_template("clientes/form.html", datos={},
                           tipos_doc=TIPOS_DOC, calificaciones=CALIFICACIONES,
                           tipos_tasa=TIPOS_TASA, modo="nuevo",
                           active_section="clientes")

@app.route("/clientes/<int:cid>/editar", methods=["GET", "POST"])
def cliente_editar(cid):
    from config import TIPOS_DOC, CALIFICACIONES, TIPOS_TASA
    from controllers.cliente_controller import guardar_cliente, obtener
    if request.method == "POST":
        datos = request.form.to_dict()
        try:
            guardar_cliente(datos, cliente_id=cid)
            flash("Cliente actualizado.", "success")
            return redirect(url_for("cliente_perfil", cid=cid))
        except Exception as e:
            return render_template("clientes/form.html", datos=datos, error=str(e),
                                   tipos_doc=TIPOS_DOC, calificaciones=CALIFICACIONES,
                                   tipos_tasa=TIPOS_TASA, modo="editar", cliente_id=cid,
                                   active_section="clientes")
    cliente = obtener(cid)
    return render_template("clientes/form.html", datos=cliente,
                           tipos_doc=TIPOS_DOC, calificaciones=CALIFICACIONES,
                           tipos_tasa=TIPOS_TASA, modo="editar", cliente_id=cid,
                           active_section="clientes")

@app.route("/clientes/<int:cid>")
def cliente_perfil(cid):
    from controllers.cliente_controller import obtener
    from controllers.prestamo_controller import listar
    cliente = obtener(cid)
    prestamos = listar(cliente_id=cid)
    return render_template("clientes/perfil.html", cliente=cliente,
                           prestamos=prestamos, active_section="clientes")

# ── Préstamos ─────────────────────────────────────────────────────────────────

ESTADOS_PRESTAMO = ["ACTIVO", "AL_DIA", "VENCIDO", "CANCELADO", "REFINANCIADO"]

@app.route("/prestamos")
def prestamos_lista():
    q      = request.args.get("q", "").strip()
    estado = request.args.get("estado", "")
    from controllers.prestamo_controller import buscar, listar
    rows = buscar(q) if q else listar(estado=estado or None)
    return render_template("prestamos/lista.html", prestamos=rows, q=q,
                           estado=estado, estados=ESTADOS_PRESTAMO,
                           active_section="prestamos")

@app.route("/prestamos/nuevo", methods=["GET", "POST"])
def prestamo_nuevo():
    from config import FRECUENCIAS, TIPOS_AMORT, TIPOS_TASA
    from controllers.cliente_controller import todos as todos_clientes
    if request.method == "POST":
        datos      = request.form.to_dict()
        cliente_id = int(datos.pop("cliente_id", 0))
        try:
            from controllers.prestamo_controller import crear
            pid = crear(cliente_id, datos)
            flash("Préstamo creado correctamente.", "success")
            return redirect(url_for("prestamo_detalle", pid=pid))
        except Exception as e:
            clientes = todos_clientes()
            return render_template("prestamos/form.html", datos=datos, error=str(e),
                                   clientes=clientes, frecuencias=FRECUENCIAS,
                                   tipos_amort=TIPOS_AMORT, tipos_tasa=TIPOS_TASA,
                                   cliente_id=cliente_id, active_section="prestamos")
    clientes   = todos_clientes()
    cliente_id = request.args.get("cliente_id", "")
    return render_template("prestamos/form.html", datos={},
                           clientes=clientes, frecuencias=FRECUENCIAS,
                           tipos_amort=TIPOS_AMORT, tipos_tasa=TIPOS_TASA,
                           cliente_id=cliente_id, active_section="prestamos")

@app.route("/prestamos/preview", methods=["POST"])
def prestamo_preview():
    """HTMX: tabla de amortización sin guardar."""
    datos = request.form.to_dict()
    try:
        from controllers.prestamo_controller import previsualizar
        resultado = previsualizar(datos)
        return render_template("_partials/tabla_amortizacion.html", resultado=resultado)
    except Exception as e:
        return f'<p class="text-red-600 p-4 font-medium">⚠ {e}</p>'

@app.route("/prestamos/<int:pid>")
def prestamo_detalle(pid):
    from controllers.prestamo_controller import obtener, cuotas
    from controllers.pago_controller import historial_pagos_prestamo
    prestamo     = obtener(pid)
    tabla_cuotas = cuotas(pid)
    pagos        = historial_pagos_prestamo(pid)
    return render_template("prestamos/detalle.html", prestamo=prestamo,
                           cuotas=tabla_cuotas, pagos=pagos,
                           active_section="prestamos")

# ── Caja ──────────────────────────────────────────────────────────────────────

@app.route("/caja")
def caja():
    from controllers.caja_controller import caja_activa
    caja_abierta = caja_activa()
    if caja_abierta:
        from database.seed import get_config
        moneda = get_config("moneda_simbolo") or "RD$"
        return render_template("caja/cobro.html", caja=caja_abierta,
                               moneda=moneda, active_section="caja")
    return render_template("caja/apertura.html", active_section="caja")

@app.route("/caja/apertura", methods=["POST"])
def caja_apertura():
    from controllers.caja_controller import abrir
    try:
        monto = float(request.form.get("monto_apertura", 0) or 0)
        abrir(monto)
        flash("Caja abierta correctamente.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("caja"))

@app.route("/caja/buscar")
def caja_buscar():
    """HTMX: busca préstamos activos."""
    q = request.args.get("q", "").strip()
    if not q:
        return ""
    from controllers.prestamo_controller import buscar
    activos = ("ACTIVO", "AL_DIA", "VENCIDO")
    resultados = [r for r in buscar(q) if r["estado"] in activos][:20]
    return render_template("_partials/resultados_prestamos.html", resultados=resultados)

@app.route("/caja/calcular/<int:pid>")
def caja_calcular(pid):
    """HTMX: calcula desglose de cuota o cancelación."""
    tipo = request.args.get("tipo", "CUOTA_NORMAL")
    try:
        from controllers.pago_controller import calcular_pago_cuota_normal, calcular_cancelacion
        from database.seed import get_config
        moneda = get_config("moneda_simbolo") or "RD$"
        if tipo == "CUOTA_NORMAL":
            info = calcular_pago_cuota_normal(pid)
        else:
            info = calcular_cancelacion(pid)
        return render_template("_partials/calculo_cuota.html",
                               info=info, tipo=tipo, moneda=moneda, prestamo_id=pid)
    except Exception as e:
        return f'<p class="text-red-600 p-4 font-medium">⚠ {e}</p>'

@app.route("/caja/cobrar", methods=["POST"])
def caja_cobrar():
    """HTMX: procesa el cobro."""
    try:
        pid    = int(request.form["prestamo_id"])
        tipo   = request.form["tipo"]
        metodo = request.form["metodo_pago"]
        ref    = request.form.get("referencia", "")
        from controllers.pago_controller import (
            calcular_pago_cuota_normal, cobrar_cuota_normal,
            cobrar_cancelacion_total,
        )
        from database.seed import get_config
        moneda = get_config("moneda_simbolo") or "RD$"
        if tipo == "CUOTA_NORMAL":
            info  = calcular_pago_cuota_normal(pid)
            cuota = info["cuota"]
            pago  = cobrar_cuota_normal(pid, cuota["id"], metodo, ref)
            return render_template("_partials/recibo.html", pago=pago, moneda=moneda)
        else:
            cobrar_cancelacion_total(pid, metodo, ref)
            return '''<div class="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                <p class="text-green-700 text-xl font-bold mb-3">✅ Préstamo cancelado</p>
                <p class="text-slate-500 text-sm mb-4">El préstamo ha sido saldado completamente.</p>
                <a href="/caja" class="inline-block px-5 py-2 bg-blue-600 text-white rounded-lg font-semibold text-sm">
                    Cobrar Otro
                </a></div>'''
    except Exception as e:
        return f'<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 font-medium">❌ {e}</div>'

@app.route("/caja/cerrar", methods=["POST"])
def caja_cerrar():
    from controllers.caja_controller import caja_activa, cerrar
    caja_abierta = caja_activa()
    if not caja_abierta:
        flash("No hay caja abierta.", "danger")
        return redirect(url_for("caja"))
    try:
        monto = float(request.form.get("monto_cierre", 0) or 0)
        notas = request.form.get("notas", "")
        cerrar(caja_abierta["id"], monto, notas)
        flash("Caja cerrada correctamente.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("caja"))

# ── Reportes ──────────────────────────────────────────────────────────────────

@app.route("/reportes")
def reportes():
    tab   = request.args.get("tab", "caja")
    fecha = request.args.get("fecha", date.today().isoformat())
    dias  = int(request.args.get("dias", 30) or 30)
    data  = {}
    if tab == "caja":
        from controllers.reporte_controller import caja as rep_caja
        data["reporte_caja"] = rep_caja(fecha)
        data["fecha"] = fecha
    elif tab == "mora":
        from controllers.reporte_controller import mora
        data["mora"] = mora()
    elif tab == "proyeccion":
        from controllers.reporte_controller import proyeccion
        data["proyeccion"] = proyeccion(dias)
        data["dias"] = dias
    elif tab == "historial":
        from models.caja import listar_cajas
        data["cajas"] = listar_cajas(60)
    return render_template("reportes/main.html", tab=tab, **data,
                           active_section="reportes")

@app.route("/reportes/pdf/caja")
def reporte_pdf_caja():
    fecha = request.args.get("fecha", date.today().isoformat())
    try:
        from services.pdf_generator import generar_reporte_caja
        import subprocess, platform
        path = generar_reporte_caja(fecha)
        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["open", path])
        flash("PDF generado y abierto.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("reportes", tab="caja", fecha=fecha))

@app.route("/reportes/excel/<tipo>")
def reporte_excel(tipo):
    fecha = request.args.get("fecha", date.today().isoformat())
    dias  = int(request.args.get("dias", 30) or 30)
    try:
        if tipo == "mora":
            from controllers.reporte_controller import mora
            from services.excel_exporter import exportar_mora
            path = exportar_mora(mora())
        elif tipo == "proyeccion":
            from controllers.reporte_controller import proyeccion
            from services.excel_exporter import exportar_proyeccion
            path = exportar_proyeccion(proyeccion(dias))
        else:
            from controllers.reporte_controller import caja as rep_caja
            from services.excel_exporter import exportar_caja
            path = exportar_caja(rep_caja(fecha))
        import subprocess, platform
        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["open", path])
        flash("Excel generado.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("reportes", tab=tipo, fecha=fecha, dias=dias))

# ── Configuración ─────────────────────────────────────────────────────────────

@app.route("/configuracion", methods=["GET", "POST"])
def configuracion():
    from config import TIPOS_TASA
    from database.seed import get_all_config, set_config
    if request.method == "POST":
        for clave, valor in request.form.items():
            set_config(clave, valor)
        flash("Configuración guardada.", "success")
        return redirect(url_for("configuracion"))
    conf = get_all_config()
    return render_template("configuracion.html", conf=conf, tipos_tasa=TIPOS_TASA,
                           active_section="configuracion")

# ── Backup ────────────────────────────────────────────────────────────────────

@app.route("/backup", methods=["POST"])
def hacer_backup():
    try:
        from services.backup import hacer_backup as _backup
        import subprocess, os
        path = _backup()
        flash(f"Backup guardado: {os.path.basename(path)}", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("configuracion"))

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=8080, host="127.0.0.1", use_reloader=False)
