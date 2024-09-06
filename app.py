import base64
from functools import wraps
import io
import os
import random
import secrets
import string
from time import timezone
from tkinter import Message
from flask import Flask, flash, jsonify, logging, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
import pyodbc
from flask_bcrypt import Bcrypt  
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import uuid
from woocommerce import API
from sqlalchemy.dialects.postgresql import UUID
from pytz import UTC
import sqlalchemy


app = Flask(__name__)
# Configurar el tiempo de vida de la sesión a 30 minutos
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
#Envio correo recuperar contraseña
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'turneromicelu@gmail.com'
app.config['MAIL_PASSWORD'] = 'wzif eujk wxpl novr'
app.config['MAIL_DEFAULT_SENDER'] = 'turneromicelu@gmail.com'
#cookie session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'my_session'
app.config['SECRET_KEY'] = 'yLxqdG0BGUft0Ep'
app.config['SQLALCHEMY_BINDS'] = {
    'db2':'postgresql://postgres:WeLZnkiKBsfVFvkaRHWqfWtGzvmSnOUn@viaduct.proxy.rlwy.net:35149/railway'
}
 
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  
mail = Mail(app)

recovery_codes = {}


#Modelos base de datos Plan de Beneficios
class Usuario(db.Model):
    __bind_key__ = 'db2'
    __tablename__ = 'Usuarios'
    __table_args__ = {'schema': 'plan_beneficios'}
    documento = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(50))
    telefono= db.Column(db.String(50), nullable=False)
    contraseña = db.Column(db.String(100))
    habeasdata = db.Column(db.Boolean)
    ciudad = db.Column(db.String(40))
    nombre = db.Column(db.String(50))
    rango = db.Column(db.String(50))
    estado = db.Column(db.Boolean, default=True)

class Puntos_Clientes(db.Model):
    __bind_key__ = 'db2'
    __tablename__ = 'Puntos_Clientes'
    __table_args__ = {'schema': 'plan_beneficios'}
    documento = db.Column(db.String(50), primary_key=True)
    total_puntos = db.Column(db.Integer)
    puntos_redimidos = db.Column(db.String(50))
    fecha_registro = db.Column(db.TIMESTAMP(timezone=True))
    
class historial_beneficio(db.Model):
    __bind_key__ = 'db2'
    __tablename__ = 'historial_beneficio'
    __table_args__ = {'schema': 'plan_beneficios'}
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento = db.Column(db.String(50), primary_key=True)
    valor_descuento = db.Column(db.Integer)
    puntos_utilizados = db.Column(db.Integer)
    fecha_canjeo = db.Column(db.TIMESTAMP(timezone=True))
    cupon = db.Column(db.String(70))
    
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_documento' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/recuperar_pass', methods=['GET', 'POST'])
def recuperar_pass():
    if request.method == 'POST':
        documento = request.form.get('documento')
        email = request.form.get('email')
       
        app.logger.debug(f"Intento de recuperación para documento: {documento}, email: {email}")
       
        usuario = Usuario.query.filter_by(documento=documento, email=email).first()
        if usuario:
            app.logger.info(f"Usuario encontrado: {usuario}")
            # Generar código de recuperación
            caracteres = string.ascii_uppercase + string.digits
            codigo = ''.join(secrets.choice(caracteres) for _ in range(6))
           
            # Establecer tiempo de expiración
            expiracion = datetime.now() + timedelta(minutes=15)
           
            # Guardar código con tiempo de expiración
            recovery_codes[email] = {'codigo': codigo, 'expiracion': expiracion}
           
            # Enviar correo
            try:
                msg = Message("Código de recuperación de contraseña micelu.co",
                              recipients=[email])
                msg.body = f"Tu código de recuperación es: {codigo}. Este código expirará en 15 minutos."
                mail.send(msg)
                return jsonify({
                    'success': True,
                    'message': 'Se ha enviado un código de recuperación a tu email. El código expirará en 15 minutos.'
                })
            except Exception as e:
                app.logger.error(f"Error al enviar email: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Hubo un error al enviar el código. Por favor, intenta de nuevo más tarde.'
                })
        else:
            app.logger.warning(f"No se encontró usuario para documento: {documento}, email: {email}")
            return jsonify({
                'success': False,
                'message': 'No se encontró un usuario con esos datos. Por favor, verifica la información.'
            })
    return render_template('recuperar_pass.html')

@app.route('/verificar_codigo', methods=['POST'])
def verificar_codigo():
    email = request.form.get('email')
    codigo_ingresado = request.form.get('codigo')
   
    if email in recovery_codes and recovery_codes[email]['codigo'] == codigo_ingresado:
        # Código válido, proceder con la recuperación de contraseña
        del recovery_codes[email]  # Eliminar el código usado
        return jsonify({'success': True, 'message': 'Código válido. Puedes proceder a cambiar tu contraseña.'})
    else:
        return jsonify({'success': False, 'message': 'Su codigo ha expirado o es incorrecto, Porfavor solicitar otro.'})
   
@app.route('/cambiar_contrasena', methods=['POST'])
def cambiar_contrasena():
    email = request.form.get('email')
    nueva_contrasena = request.form.get('nueva_contrasena')
   
    if len(nueva_contrasena) < 5:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 5 caracteres.'})
   
    if ' ' in (nueva_contrasena):
        return jsonify(({'success': False, 'message': 'La contraseña no puede contener espacios.'}))
   
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario:
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        usuario.contraseña = hashed_password
        db.session.commit()
        return jsonify({'success': True, 'message': 'Contraseña cambiada exitosamente.'})
    else:
        return jsonify({'success': False, 'message': 'Usuario no encontrado.'})
 
@app.route('/miperfil')
@login_required
def miperfil():
    documento_usuario = session.get('user_documento')
    
    if documento_usuario:
        usuario = Usuario.query.filter_by(documento=documento_usuario).first()
        
        if usuario:
            total_puntos = 0
            puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento_usuario).first()
            if puntos_usuario:
                puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
                total_puntos = puntos_usuario.total_puntos - puntos_redimidos
            
            return render_template('miperfil.html', usuario=usuario, total_puntos=total_puntos)
        else:
            flash('No se encontró el usuario en la base de datos.', 'error')
            return redirect(url_for('login'))
    else:
        flash('Por favor, inicia sesión para ver tu perfil.', 'error')
        return redirect(url_for('login'))
#---------------------------------------------------LOGIN-------------------------------------------------
@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    data = request.json
    field = data.get('field')
    value = data.get('value')
    documento_usuario = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento_usuario).first()
   
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
   
    if field == 'email':
        usuario.email = value
    elif field == 'telefono':
        usuario.telefono = value
    else:
        return jsonify({'success': False, 'message': 'Campo no válido'}), 400
   
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Perfil actualizado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
 
#---------------------------------------------------LOGIN-------------------------------------------------
def generate_captcha_image():
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    image = Image.new('RGB', (200, 100), color = (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 26)
    draw.text((40,30), captcha_text, font=font, fill=(0,0,0))
    for _ in range(1000):
        draw.point((random.randint(0, 200), random.randint(0, 100)), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return captcha_text, img_str
 
@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        captcha_text, captcha_image = generate_captcha_image()
        session['captcha'] = captcha_text
        return render_template('login.html', captcha_image=captcha_image)
    elif request.method == 'POST':
        documento = str(request.form.get('documento'))
        contraseña = str(request.form.get('contraseña'))
        user_captcha = request.form.get('captcha')
       
        # Verificar el captcha primero
        if user_captcha != session.get('captcha'):
            return jsonify({'status': 'error', 'message': 'Captcha incorrecto. Por favor, intenta de nuevo.'})
       
        user = Usuario.query.filter_by(documento=documento).first()
        if user and user.contraseña and contraseña:
            try:
                if bcrypt.check_password_hash(user.contraseña, contraseña):
                    session['user_documento'] = user.documento
                    # Hacer la sesión permanente pero con tiempo de vida limitado
                    session.permanent = True
                    return jsonify({'status': 'success', 'message': f'Bienvenido, {user.nombre}. Has iniciado sesión correctamente.', 'redirect_url': url_for('mhistorialcompras')})
                else:
                    return jsonify({'status': 'error', 'message': 'Contraseña incorrecta. Por favor, intenta de nuevo.'})
            except ValueError as e:
                print(f"Error al verificar la contraseña: {str(e)}")
                return jsonify({'status': 'error', 'message': 'Error al verificar la contraseña. Por favor, contacta al administrador.'})
        else:
            return jsonify({'status': 'error', 'message': 'Documento o Contraseña Incorrectos. Por favor, intenta de nuevo.'})

@app.route('/refresh_captcha', methods=['GET'])
def refresh_captcha():
    captcha_text, captcha_image = generate_captcha_image()
    session['captcha'] = captcha_text
    return jsonify({'captcha_image': captcha_image})


@app.route('/login', methods=["GET", "POST"])
def loginn():
    return render_template('login.html')

#--------------------RUTA HISTORIAL --------------------------------------------------
@app.route('/mhistorialcompras')
@login_required
def mhistorialcompras():
    documento = session.get('user_documento')
    
    if not documento:
        return redirect(url_for('login'))
    
    try:
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=20.109.21.246;"
            "DATABASE=MICELU;"
            "UID=db_read;"
            "PWD=mHRL_<='(],#aZ)T\"A3QeD;"
            "TrustServerCertificate=yes"
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Verificar si el cliente existe
        check_query = """
        SELECT COUNT(*) as count
        FROM Clientes c
        WHERE c.HABILITADO = 'S' AND c.NIT = ?
        """
        cursor.execute(check_query, documento)
        count = cursor.fetchone().count
        
        # Consulta principal
        query = """
        SELECT
            m.NOMBRE AS PRODUCTO_NOMBRE,
            m.VLRVENTA,
            m.FHCOMPRA,
            m.TIPODCTO
        FROM
            Clientes c
        JOIN
            V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
        JOIN
            Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
        WHERE
            c.HABILITADO = 'S'
            AND c.NIT = ?
            AND m.VLRVENTA > 0
            AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
        ORDER BY
            m.FHCOMPRA DESC;
        """
        
        cursor.execute(query, documento)
        results = cursor.fetchall()
        historial = []
        total_puntos_nuevos = 0
        for row in results:
            venta = float(row.VLRVENTA)
            puntos_venta = int(venta // 1000)  # 1 punto por cada 1000 pesos
            total_puntos_nuevos += puntos_venta
            tipo_documento = "Factura Medellín" if row.TIPODCTO == "FM" else "Factura Bogotá" if row.TIPODCTO == "FB" else row.TIPODCTO
            historial.append({
                "PRODUCTO_NOMBRE": row.PRODUCTO_NOMBRE,
                "VLRVENTA": venta,
                "FHCOMPRA": row.FHCOMPRA.strftime('%Y-%m-%d'),
                "PUNTOS_GANADOS": puntos_venta,
                "TIPODCTO": tipo_documento
            })
        
        cursor.close()
        conn.close()

        # Actualizar puntos en la base de datos
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            puntos_usuario.total_puntos = total_puntos_nuevos
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            total_puntos = total_puntos_nuevos - puntos_redimidos
            db.session.commit()
        else:
            nuevo_usuario = Puntos_Clientes(documento=documento, total_puntos=total_puntos_nuevos, puntos_redimidos='0')
            db.session.add(nuevo_usuario)
            db.session.commit()
            total_puntos = total_puntos_nuevos
        
        return render_template('mhistorialcompras.html', historial=historial, total_puntos=total_puntos)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return "Ha ocurrido un error al procesar su solicitud.", 500
    
@app.route('/mpuntosprincipal')
@login_required
def mpuntosprincipal():
    # Asumimos que el documento del usuario está en la sesión
    documento = session.get('user_documento')
    
    total_puntos = 0
    if documento:
        # Consulta a la base de datos para obtener los puntos del usuario
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            total_puntos = puntos_usuario.total_puntos - puntos_redimidos
    
    # Lista de IDs de productos que queremos mostrar
    product_ids = [154814, 154809, 154774, 154765, 154752, 154613, 154765]
    
    # Obtener productos de WooCommerce
    try:
        wcapi = API(
            url="https://micelu.co",
            consumer_key="ck_24e1d02972506069aec3b589f727cc58636491df",
            consumer_secret="cs_8bd38a861efefc56403c7899d5303c3351c9e028",
            version="wc/v3",
            timeout=30
        )
        
        # Consultar todos los productos de una vez
        response = wcapi.get("products", params={"include": ",".join(map(str, product_ids))})
        
        if response.status_code == 200:
            wc_products = response.json()
            products = []
            for wc_product in wc_products:
                product = {
                    'id': wc_product['id'],
                    'name': wc_product['name'],
                    'price': wc_product['price'],
                    'description': wc_product['description'],
                    'short_description': wc_product['short_description'],
                    'color': wc_product['attributes'][0]['options'][0] if wc_product['attributes'] else 'N/A',
                    'image_url': wc_product['images'][0]['src'] if wc_product['images'] else url_for('static', filename='images/placeholder.png'),
                    'points': int(float(wc_product['price'])/1000)  # Asumiendo que 1 punto = 1000 pesos
                }
                products.append(product)
        else:
            products = []
    except Exception as e:
        products = []
    
    
    return render_template('mpuntosprincipal.html', total_puntos=total_puntos, products=products)

#Ruta para manejar el descuento de los puntos

from datetime import datetime
import uuid

wcapi = API(
    url="https://micelu.co",
    consumer_key="ck_4a0a6ac32a9cbfe9d5f0dd4a029312e0893e22a7",
    consumer_secret="cs_e7d06f5199b3982b3e02234cc305a8f2d0b71dd0",
    version="wc/v3"
)

wcapi = API(
    url="https://micelu.co",
    consumer_key="ck_4a0a6ac32a9cbfe9d5f0dd4a029312e0893e22a7",
    consumer_secret="cs_e7d06f5199b3982b3e02234cc305a8f2d0b71dd0",
    version="wc/v3"
)

from woocommerce import API
import uuid
from datetime import datetime, timedelta
import random
import string

# Configuración de la API de WooCommerce
wcapi = API(
    url="https://micelu.co",
    consumer_key="ck_4a0a6ac32a9cbfe9d5f0dd4a029312e0893e22a7",
    consumer_secret="cs_e7d06f5199b3982b3e02234cc305a8f2d0b71dd0",
    version="wc/v3"
)

@app.route('/redimir_puntos', methods=['POST'])
@login_required
def redimir_puntos():
    try:
        documento = session.get('user_documento')
        puntos_a_redimir = int(request.json.get('points'))
        codigo = request.json.get('code')  # Obtener el código del frontend
        
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if not puntos_usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
        total_puntos = puntos_usuario.total_puntos
        puntos_disponibles = total_puntos - puntos_redimidos
        
        if puntos_a_redimir > puntos_disponibles:
            return jsonify({'success': False, 'message': 'No tienes suficientes puntos'}), 400
        
        # Actualizar puntos redimidos
        puntos_usuario.puntos_redimidos = str(puntos_redimidos + puntos_a_redimir)
        
        # Calcular descuento
        descuento = puntos_a_redimir * 100  # Asumiendo que cada punto vale 100 unidades de moneda
        
        # Crear cupón en WooCommerce
        woo_coupon = create_woo_coupon(codigo, descuento)
        
        if not woo_coupon:
            return jsonify({'success': False, 'message': 'Error al crear el cupón en WooCommerce'}), 500
        
        # Crear nuevo registro en historial_beneficio
        nuevo_historial = historial_beneficio(
            id=uuid.uuid4(),
            documento=documento,
            valor_descuento=descuento,
            puntos_utilizados=puntos_a_redimir,
            fecha_canjeo=datetime.now(),
            cupon=codigo
        )
        
        # Agregar el nuevo registro a la sesión y hacer commit
        db.session.add(nuevo_historial)
        db.session.commit()
        
        new_total = puntos_disponibles - puntos_a_redimir
        return jsonify({
            'success': True, 
            'new_total': new_total,
            'codigo': codigo,
            'descuento': descuento
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Error al redimir puntos'}), 500

def create_woo_coupon(code, amount):
    try:
        data = {
            "code": code,
            "discount_type": "fixed_cart",
            "amount": str(amount),
            "individual_use": True,
            "exclude_sale_items": True,
            "usage_limit": 1,
            "date_expires": (datetime.now() + timedelta(hours=12)).isoformat()
        }
        
        response = wcapi.post("coupons", data).json()
        
        if 'id' in response:
            return response
        else:
            print(f"Error al crear cupón: {response}")
            return None
    except Exception as e:
        print(f"Error al crear cupón en WooCommerce: {e}")
        return None
    
@app.route('/quesonpuntos')
@login_required
def quesonpuntos():
    documento = session.get('user_documento')
    total_puntos = 0
    if documento:
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            total_puntos = puntos_usuario.total_puntos - puntos_redimidos
    return render_template('puntos.html',total_puntos=total_puntos)

@app.route('/homepuntos')
@login_required
def homepuntos():
    documento = session.get('user_documento')
    total_puntos = 0
    if documento:
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            total_puntos = puntos_usuario.total_puntos - puntos_redimidos
    return render_template('home.html',total_puntos=total_puntos)

@app.route('/logout')
@login_required
def logout():
    session.pop('user_documento', None)
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))

#----------------------------------CREAR CONTRASEÑA----------------------------------
@app.route('/crear_pass', methods=['GET', 'POST'])
def crear_pass():
    if request.method == 'POST':
        documento = request.form['documento']
        contraseña = request.form['contraseña']
        confirmar_contraseña = request.form['confirmar_contraseña']
        habeasdata = 'habeasdata' in request.form
       
        # Verificaciones existentes (sin cambios)
        if contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('crear_pass'))
       
        if len(contraseña) <= 4:
            flash('La contraseña debe tener más de 5 caracteres', 'danger')
            return redirect(url_for('crear_pass'))
       
        if ' ' in contraseña:
            flash('La contraseña no puede contener espacios', 'danger')
            return redirect(url_for('crear_pass'))
       
        usuario_existente = Usuario.query.filter_by(documento=documento).first()
        if usuario_existente:
            flash('Este documento ya ha sido registrado', 'danger')
            return redirect(url_for('crear_pass'))
       
        try:
            # Crear el usuario en la tabla original
            usuario_creado = crear_usuario(documento, contraseña, habeasdata)
           
            if usuario_creado:
                # Crear el registro en la tabla Puntos_Clientes
                nuevo_punto_cliente = Puntos_Clientes(
                    documento=documento,
                    total_puntos='0',
                    fecha_registro=datetime.now(UTC),
                    puntos_redimidos='0'
                )
                db.session.add(nuevo_punto_cliente)
                db.session.commit()
               
                flash('Usuario creado exitosamente. <a href="/" class="alert-link">Inicia sesión aquí</a>', 'success')
            else:
                flash('Cédula no registrada. Por favor, registre una compra', 'warning')
           
            return redirect(url_for('crear_pass'))
       
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash('Este documento ya ha sido registrado', 'danger')
        except sqlalchemy.exc.DataError as e:
            db.session.rollback()
            flash('Error en el formato de los datos. Por favor, revise la información ingresada.', 'danger')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error al crear el usuario: {str(e)}')
            flash('Ocurrió un error al crear el usuario. Por favor, inténtelo de nuevo.', 'danger')
       
        return redirect(url_for('crear_pass'))
   
    return render_template('crear_pass.html')


def crear_usuario(cedula, contraseña, habeasdata):
    try:
        # Conexión a la base de datos
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=20.109.21.246;"
            "DATABASE=MICELU;"
            "UID=db_read;"
            "PWD=mHRL_<='(],#aZ)T\"A3QeD;"
            "TrustServerCertificate=yes"
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Consulta SQL con parámetro
        query = """
        SELECT DISTINCT
            c.NOMBRE AS CLIENTE_NOMBRE,
            c.NIT,
            c.TEL1 AS telefono,
            c.EMAIL,
            c.CIUDAD,
            c.DescripTipoCli
        FROM
            Clientes c
        JOIN
            Canal cn ON c.CANAL = cn.CODCANAL
        JOIN
            V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
        JOIN
            Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
        JOIN
            MtMercia mt ON m.PRODUCTO=mt.CODIGO
        WHERE
            c.HABILITADO = 'S'
            AND c.CIUDAD IN ('05001', '11001')
            AND (m.TIPODCTO='FM' OR m.TIPODCTO='FB')
            AND m.VLRVENTA>0
            AND c.NIT = ?
        ORDER BY
            c.NOMBRE;
        """

        # Ejecutar la consulta con el parámetro de cédula
        cursor.execute(query, (cedula,))

        # Obtener todos los resultados
        results = cursor.fetchall()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        # Si no hay resultados, la cédula no está registrada
        if not results:
            return False

        with app.app_context():
            with db.session.begin():
                for row in results:
                    if row.CIUDAD == '05001':
                        ciudad = 'Medellin'
                    elif row.CIUDAD == '11001':
                        ciudad = 'Bogota'
                    else:
                        ciudad = 'No identificado'

                    clave=bcrypt.generate_password_hash(contraseña).decode('utf-8')
                    
                    nuevo_usuario = Usuario(
                        documento=row.NIT.strip() if row.NIT else None,
                        email=row.EMAIL.strip() if row.EMAIL else None,
                        telefono=row.telefono.strip() if row.telefono else None,
                        contraseña=clave,
                        habeasdata=habeasdata,
                        ciudad=ciudad,
                        nombre=row.CLIENTE_NOMBRE.strip() if row.CLIENTE_NOMBRE else None,
                        rango=row.DescripTipoCli.strip() if row.DescripTipoCli else None,
                        estado=True
                    )
                    db.session.add(nuevo_usuario)
                    db.session.commit()

        return True

    except pyodbc.Error as e:
        print("Error al conectarse a la base de datos:", e)
        raise e
    except Exception as e:
        print("Error al crear el usuario:", e)
        raise e
#------------------funciones para traer informacion del carrusel------------------------------------------------
def get_product_info(product_id):
    try:
        wcapi = API(
            url="https://micelu.co",
            consumer_key="ck_24e1d02972506069aec3b589f727cc58636491df",
            consumer_secret="cs_8bd38a861efefc56403c7899d5303c3351c9e028",
            version="wc/v3",
            timeout=30
        )
       
        response = wcapi.get(f"products/{product_id}")
        if response.status_code == 200:
            wc_product = response.json()
            product = {
                'id': wc_product['id'],
                'name': wc_product['name'],
                'price': wc_product['price'],
                'description': wc_product['description'],
                'short_description': wc_product['short_description'],
                'color': wc_product['attributes'][0]['options'][0] if wc_product['attributes'] else 'N/A',
                'image_url': wc_product['images'][0]['src'] if wc_product['images'] else url_for('static', filename='images/placeholder.png'),
                'points': int(float(wc_product['price']) * 0.01),  # Asumiendo que 1 punto = 1% del precio
                'attributes': wc_product['attributes']
            }
            return product
        else:
            print(f"Error al obtener el producto {product_id}: {response.text}")
            return None
    except Exception as e:
        print(f"Error al obtener producto de WooCommerce: {str(e)}")
        return None

    #----------------------------------- mpuntosprincipal-----------------------------
@app.route('/redime_ahora')
def redime_ahora():
    documento_usuario = session.get('user_documento')
    
    if documento_usuario:
        usuario = Usuario.query.filter_by(documento=documento_usuario).first()
        
        if usuario:
            total_puntos = 0
            puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento_usuario).first()
            if puntos_usuario:
                puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
                total_puntos = puntos_usuario.total_puntos - puntos_redimidos
    return render_template("redime_ahora.html",total_puntos=total_puntos)

@app.route('/acumulapuntos')
def acumulapuntos():
    return render_template("acumulapuntos.html")

@app.route('/redimir')
def redimiendo():
    return render_template("redimir.html")
    


if __name__ == '__main__':
    app.run(debug=True)