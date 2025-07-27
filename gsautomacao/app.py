from flask import Flask, request, jsonify, send_from_directory
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import sqlite3
import os
import traceback
import smtplib

# Configurações de email
EMAIL_CONFIG = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'user': 'sysggoldensat@gmail.com',
    'password': 'yzxs ieko subp xesu'
}

# Configuração do Flask com pasta static explícita
app = Flask(__name__, static_folder='static', static_url_path='')

def init_db():
    conn = sqlite3.connect('formularios.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS formularios')
    c.execute('''
        CREATE TABLE formularios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT NOT NULL,
            empresa TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            produto TEXT NOT NULL,
            aceite_termo BOOLEAN NOT NULL,
            aceite_contrato BOOLEAN NOT NULL,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def enviar_email(dados):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_CONFIG['user']
    msg['To'] = dados['email']
    msg['Subject'] = 'Novo formulário recebido'

    corpo_email = f"""
    CNPJ: {dados['cnpj']}
    Empresa: {dados['empresa']}
    Email: {dados['email']}
    Telefone: {dados['telefone']}
    Produto: {dados['produto']}
    """

    msg.attach(MIMEText(corpo_email, 'plain'))

    # Anexar PDF fixo da pasta static
    pdf_path = os.path.join('static', 'gs-400.pdf')
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            part = MIMEApplication(f.read(), _subtype='pdf')
            part.add_header('Content-Disposition', 'attachment', filename='gs-400.pdf')
            msg.attach(part)

    if 'pdf' in request.files:
        pdf = request.files['pdf']
        if pdf.filename != '':
            pdf_data = pdf.read()
            pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf.filename)
            msg.attach(pdf_attachment)

    try:
        server = smtplib.SMTP(EMAIL_CONFIG['host'], EMAIL_CONFIG['port'])
        server.starttls()
        server.login(EMAIL_CONFIG['user'], EMAIL_CONFIG['password'])
        server.sendmail(EMAIL_CONFIG['user'], dados['email'], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/salvar-formulario', methods=['POST'])
def salvar_formulario():
    try:
        dados = {
            'cnpj': request.form.get('cnpj'),
            'empresa': request.form.get('empresa'),
            'email': request.form.get('email'),
            'telefone': request.form.get('telefone'),
            'produto': request.form.get('produto'),
            'aceiteTermo': request.form.get('aceiteTermo') == 'true',
            'aceiteContrato': request.form.get('aceiteContrato') == 'true'
        }
        
        # Verificar aceites
        if not dados['aceiteTermo'] or not dados['aceiteContrato']:
            return jsonify({'success': False, 'message': 'É necessário aceitar os termos e o contrato'}), 400
        
        # Salvar no banco de dados
        conn = sqlite3.connect('formularios.db')
        c = conn.cursor()
        c.execute('''INSERT INTO formularios (cnpj, empresa, email, telefone, produto, aceite_termo, aceite_contrato)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (dados['cnpj'], dados['empresa'], dados['email'], dados['telefone'],
                   dados['produto'], dados['aceiteTermo'], dados['aceiteContrato']))
        conn.commit()
        conn.close()

        # Enviar email
        if enviar_email(dados):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar e-mail'})

    except Exception as e:
        print('Erro ao processar formulário:', e)
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 