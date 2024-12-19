import os
import sqlite3
from flask import Flask, render_template, request, redirect, flash, url_for
from flask import jsonify


# Configuração do Flask
app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configuração do caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório do arquivo app.py
DB_NAME = os.path.join(BASE_DIR, 'database/products_system.db')  # Caminho absoluto para o banco

# Criação da pasta 'database' caso não exista
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)

# Configuração do diretório de upload
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')  # Caminho absoluto para a pasta uploads
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criação da pasta 'uploads' caso não exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Inicialização do banco de dados (exemplo)
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Criar a tabela 'products' com todas as colunas necessárias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT,
                ean TEXT,
                descricao TEXT,
                categoria TEXT,
                marca TEXT,
                modelo TEXT,
                cor TEXT,
                faixa_etaria TEXT,
                genero TEXT,
                nome_comercial TEXT
            )
        ''')

        # Verificar colunas existentes e adicionar as faltantes
        cursor.execute("PRAGMA table_info(products)")
        existing_columns = [column[1] for column in cursor.fetchall()]

        required_columns = ["categoria", "marca", "modelo", "cor", "faixa_etaria", "genero", "nome_comercial"]
        for column in required_columns:
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {column} TEXT")
                print(f"Coluna '{column}' adicionada ao banco de dados.")

        conn.commit()
        print("Banco de dados atualizado com sucesso!")

        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_custom_field_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                campo_id INTEGER NOT NULL,
                valor_id INTEGER NOT NULL,
                UNIQUE(produto_id, campo_id)
            )
        """)
        conn.commit()

        cursor.execute('''
    CREATE TABLE IF NOT EXISTS custom_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'manual'
            )
        ''')
        print("tabbela manual criada e acessada.")

        # Criar tabela 'custom_fields'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL
            )
        ''')
        print("Tabela 'custom_fields' criada/verificada.")

        # Criar tabela 'custom_values'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campo_id INTEGER NOT NULL,
                valor TEXT NOT NULL,
                FOREIGN KEY (campo_id) REFERENCES custom_fields(id)
            )
        ''')
        print("Tabela 'custom_values' criada/verificada.")

        # Criar tabela 'product_custom_field_values'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_custom_field_values (
                produto_id INTEGER NOT NULL,
                campo_id INTEGER NOT NULL,
                valor_id INTEGER NOT NULL,
                PRIMARY KEY (produto_id, campo_id),
                FOREIGN KEY (produto_id) REFERENCES products(id),
                FOREIGN KEY (campo_id) REFERENCES custom_fields(id),
                FOREIGN KEY (valor_id) REFERENCES custom_values(id)
            )
        ''')
        print("Tabela 'product_custom_field_values' criada/verificada.")

    print("Banco de dados inicializado com sucesso!")

# Função para processar o arquivo XML
import xml.etree.ElementTree as ET  # Certifique-se de que já importou este módulo

def processar_xml(file_path):
    print(f"Processando o arquivo XML: {file_path}")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'ns': 'http://www.portalfiscal.inf.br/nfe'}

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            for det in root.findall('.//ns:det', namespace):
                produto = {
                    'codigo': det.find('.//ns:cProd', namespace).text,
                    'ean': det.find('.//ns:cEAN', namespace).text,
                    'descricao': det.find('.//ns:xProd', namespace).text,
                    'ncm': det.find('.//ns:NCM', namespace).text,
                    'cfop': det.find('.//ns:CFOP', namespace).text,
                    'quantidade': float(det.find('.//ns:qCom', namespace).text),
                    'preco_unitario': float(det.find('.//ns:vUnCom', namespace).text),
                    'preco_total': float(det.find('.//ns:vProd', namespace).text),
                    'icms_base': float(det.find('.//ns:vBC', namespace).text),
                    'icms_percentual': float(det.find('.//ns:pICMS', namespace).text),
                    'icms_valor': float(det.find('.//ns:vICMS', namespace).text),
                    'ipi_base': float(det.find('.//ns:vBCIPI', namespace).text) if det.find('.//ns:vBCIPI', namespace) is not None else 0.0,
                    'ipi_percentual': float(det.find('.//ns:pIPI', namespace).text) if det.find('.//ns:pIPI', namespace) is not None else 0.0,
                    'ipi_valor': float(det.find('.//ns:vIPI', namespace).text) if det.find('.//ns:vIPI', namespace) is not None else 0.0
                }

                print(f"Inserindo produto: {produto}")  # Log do produto processado
                cursor.execute('''
                    INSERT INTO products (codigo, ean, descricao, ncm, cfop, quantidade, preco_unitario,
                    preco_total, icms_base, icms_percentual, icms_valor,
                    ipi_base, ipi_percentual, ipi_valor)
                    VALUES (:codigo, :ean, :descricao, :ncm, :cfop, :quantidade, :preco_unitario,
                    :preco_total, :icms_base, :icms_percentual, :icms_valor,
                    :ipi_base, :ipi_percentual, :ipi_valor)
                ''', produto)
            conn.commit()
        print("XML processado com sucesso!")
    except Exception as e:
        print(f"Erro ao processar o XML: {e}")

def gerar_nome_comercial(produto_dict):
    # Garantir que todos os campos sejam strings válidas
    partes = [
        produto_dict.get('categoria', '').strip() or 'Sem Categoria',
        produto_dict.get('marca', '').strip() or 'Sem Marca',
        produto_dict.get('modelo', '').strip() or 'Sem Modelo',
        produto_dict.get('cor', '').strip() or 'Sem Cor',
        produto_dict.get('faixa_etaria', '').strip() or 'Sem Faixa Etária',
        produto_dict.get('genero', '').strip() or 'Sem Gênero'
    ]
    # Retornar o nome comercial com as partes separadas por espaços
    return ' '.join(partes).strip()

def gerar_nome_comercial(produto_dict):
    print(f"Recebendo produto_dict: {produto_dict}")
    nome_comercial = f"{produto_dict['categoria']} {produto_dict['marca']} {produto_dict['modelo']} {produto_dict['cor']} {produto_dict['faixa_etaria']} {produto_dict['genero']}".strip()
    print(f"Gerado nome_comercial: {nome_comercial}")
    return nome_comercial if nome_comercial else "Sem Informações"

# Rota para gerenciar valores de campos personalizados

@app.route('/custom_fields', methods=['GET', 'POST'])
def custom_fields():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            nome = request.form.get('nome')
            tipo = request.form.get('tipo', 'manual')

            if not nome or not nome.strip():
                flash("Erro: O nome do campo não pode estar vazio.", "error")
            else:
                try:
                    cursor.execute("INSERT INTO custom_fields (nome, tipo) VALUES (?, ?)", (nome.strip(), tipo))
                    conn.commit()
                    flash(f"Campo '{nome}' criado com sucesso!", "success")
                except sqlite3.Error as e:
                    flash(f"Erro ao criar campo: {e}", "error")

        cursor.execute("SELECT id, nome, tipo FROM custom_fields")
        campos = cursor.fetchall()

    return render_template('custom_fields.html', campos=campos)

# Rota para editar um campo personalizado
@app.route('/editar_campo/<int:campo_id>', methods=['GET', 'POST'])
def editar_campo(campo_id):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            if request.method == 'POST':
                novo_nome = request.form.get('nome')
                tipo = request.form.get('tipo')

                if not novo_nome or not tipo:
                    flash("Erro: Todos os campos precisam ser preenchidos.", "error")
                    return redirect(request.url)

                cursor.execute("UPDATE custom_fields SET nome = ?, tipo = ? WHERE id = ?", (novo_nome, tipo, campo_id))
                conn.commit()
                flash("Campo atualizado com sucesso!", "success")
                return redirect(url_for('custom_fields'))

            # Buscar o campo para edição
            cursor.execute("SELECT id, nome, tipo FROM custom_fields WHERE id = ?", (campo_id,))
            campo = cursor.fetchone()

            if not campo:
                flash("Erro: Campo não encontrado.", "error")
                return redirect(url_for('custom_fields'))

        return render_template('editar_campo.html', campo=campo)

    except Exception as e:
        flash(f"Erro ao editar o campo: {e}", "error")
        return redirect(url_for('custom_fields'))
    
@app.route('/atualizar_nome_comercial', methods=['POST'])
def atualizar_nome_comercial():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Selecionar todos os produtos
            cursor.execute("""
                SELECT id, categoria, marca, modelo, cor, faixa_etaria, genero 
                FROM products
            """)
            produtos = cursor.fetchall()

            total_atualizados = 0
            for produto in produtos:
                produto_id = produto[0]
                produto_dict = {
                    "categoria": produto[1] if produto[1] else '',
                    "marca": produto[2] if produto[2] else '',
                    "modelo": produto[3] if produto[3] else '',
                    "cor": produto[4] if produto[4] else '',
                    "faixa_etaria": produto[5] if produto[5] else '',
                    "genero": produto[6] if produto[6] else ''
                }
                nome_comercial = gerar_nome_comercial(produto_dict)
                cursor.execute("""
                    UPDATE products 
                    SET nome_comercial = ? 
                    WHERE id = ?
                """, (nome_comercial, produto_id))
                total_atualizados += 1

                # Log para debug
                print(f"Produto ID {produto_id} atualizado com Nome Comercial: {nome_comercial}")

            conn.commit()
            flash(f"Nomes comerciais atualizados com sucesso! Total: {total_atualizados}", "success")
    except Exception as e:
        print(f"Erro ao atualizar nomes comerciais: {e}")
        flash("Erro ao atualizar nomes comerciais.", "error")

    return redirect(url_for('produtos'))



# Rota para editar um valor de campo personalizado
@app.route('/editar_valor/<int:valor_id>', methods=['GET', 'POST'])
def editar_valor(valor_id):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            if request.method == 'POST':
                novo_valor = request.form.get('valor')

                if not novo_valor:
                    flash("Erro: O valor não pode estar vazio.", "error")
                    return redirect(request.url)

                cursor.execute("UPDATE custom_values SET valor = ? WHERE id = ?", (novo_valor, valor_id))
                conn.commit()
                flash("Valor atualizado com sucesso!", "success")
                return redirect(url_for('custom_fields'))

            # Buscar o valor atual
            cursor.execute("SELECT id, valor FROM custom_values WHERE id = ?", (valor_id,))
            valor = cursor.fetchone()

            if not valor:
                flash("Erro: Valor não encontrado.", "error")
                return redirect(url_for('custom_fields'))

        return render_template('editar_valor.html', valor=valor)

    except Exception as e:
        flash(f"Erro ao editar o valor: {e}", "error")
        return redirect(url_for('custom_fields'))


@app.route('/excluir_campo/<int:campo_id>', methods=['POST'])
def excluir_campo(campo_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM custom_values WHERE campo_id = ?", (campo_id,))
            cursor.execute("DELETE FROM product_custom_field_values WHERE campo_id = ?", (campo_id,))
            cursor.execute("DELETE FROM custom_fields WHERE id = ?", (campo_id,))
            conn.commit()
            flash("Campo excluído com sucesso!", "success")
        except sqlite3.Error as e:
            flash(f"Erro ao excluir o campo: {e}", "error")

    return redirect(url_for('custom_fields'))

@app.route('/custom_fields/<int:campo_id>/values', methods=['GET', 'POST'])
def custom_field_values(campo_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Verificar campo específico
        cursor.execute("SELECT id, nome FROM custom_fields WHERE id = ?", (campo_id,))
        campo = cursor.fetchone()
        if not campo:
            flash("Campo não encontrado!", "error")
            return redirect(url_for('custom_fields'))

        # Adicionar valor ao campo
        if request.method == 'POST':
            valor = request.form.get('valor')
            if valor:
                cursor.execute("INSERT INTO custom_values (campo_id, valor) VALUES (?, ?)", (campo_id, valor))
                conn.commit()
                flash(f"Valor '{valor}' adicionado com sucesso!", "success")
            else:
                flash("Erro: O valor não pode estar vazio!", "error")

        # Recuperar os valores existentes
        cursor.execute("SELECT id, valor FROM custom_values WHERE campo_id = ?", (campo_id,))
        valores = cursor.fetchall()

    return render_template('custom_field_values.html', campo=campo, valores=valores)


@app.route('/produtos', methods=['GET'])
def produtos():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Consultar produtos
            cursor.execute("""
                SELECT id, codigo, ean, descricao, categoria, marca, modelo, cor, faixa_etaria, genero, nome_comercial
                FROM products
            """)
            produtos = cursor.fetchall()

            # Consultar campos personalizados
            cursor.execute("SELECT id, nome FROM custom_fields")
            campos_personalizados = cursor.fetchall()

            # Consultar valores de campos personalizados
            cursor.execute("SELECT campo_id, id, valor FROM custom_values")
            valores_brutos = cursor.fetchall()

            valores_personalizados = {}
            for campo_id, valor_id, valor in valores_brutos:
                if campo_id not in valores_personalizados:
                    valores_personalizados[campo_id] = []
                valores_personalizados[campo_id].append({"id": valor_id, "valor": valor})

        # Renderizar template
        return render_template(
            'produtos.html',
            produtos=produtos,
            campos_personalizados=campos_personalizados,
            valores_personalizados=valores_personalizados
        )
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
        flash("Erro ao carregar os produtos.", "error")
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Erro geral: {e}")
        flash("Erro desconhecido ao acessar a página de produtos.", "error")
        return redirect(url_for('index'))


@app.route('/atualizar_valor', methods=['POST'])
def atualizar_valor():
    """
    Atualiza os valores personalizados para os produtos
    """
    try:
        produto_id = request.form.get('produto_id')
        campo_id = request.form.get('campo_id')
        valor_id = request.form.get('valor_id')

        print(f"Recebido - Produto ID: {produto_id}, Campo ID: {campo_id}, Valor ID: {valor_id}")

        if not produto_id or not campo_id or not valor_id:
            flash("Erro: Todos os campos precisam ser preenchidos", "error")
            return redirect('/produtos')

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Verifica se o registro já existe
            cursor.execute("""
                SELECT * FROM product_custom_field_values 
                WHERE produto_id = ? AND campo_id = ?
            """, (produto_id, campo_id))
            existe = cursor.fetchone()

            if existe:
                # Atualiza o valor existente
                cursor.execute("""
                    UPDATE product_custom_field_values
                    SET valor_id = ?
                    WHERE produto_id = ? AND campo_id = ?
                """, (valor_id, produto_id, campo_id))
                flash("Valor atualizado com sucesso!", "success")
            else:
                # Insere um novo valor
                cursor.execute("""
                    INSERT INTO product_custom_field_values (produto_id, campo_id, valor_id)
                    VALUES (?, ?, ?)
                """, (produto_id, campo_id, valor_id))
                flash("Valor salvo com sucesso!", "success")

            conn.commit()

    except Exception as e:
        print(f"Erro ao salvar o valor: {e}")
        flash(f"Erro ao salvar o valor: {e}", "error")

    return redirect('/produtos')

@app.route('/salvar_todos', methods=['POST'])
def salvar_todos():
    try:
        data = request.get_json()
        print("Dados recebidos no backend:", data)

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            for item in data['valores']:
                produto_id = item.get('produto_id')
                campo_id = item.get('campo_id')
                valor_id = item.get('valor_id')

                if produto_id and campo_id and valor_id:  # Validação dos dados
                    cursor.execute("""
                        INSERT OR REPLACE INTO product_custom_field_values (produto_id, campo_id, valor_id)
                        VALUES (?, ?, ?)
                    """, (produto_id, campo_id, valor_id))

            conn.commit()
        return jsonify({'status': 'success', 'message': 'Valores salvos com sucesso!'})
    except Exception as e:
        print("Erro ao salvar os valores:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/salvar_tabela_produtos', methods=['POST'])
def salvar_tabela_produtos():
    try:
        data = request.json  # Captura os dados enviados pelo frontend
        produtos = data.get('produtos', [])

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            for produto in produtos:
                produto_id = produto.get('produto_id')
                nome_comercial = produto.get('nome_comercial', '').strip()

                # Atualiza o banco de dados apenas se houver um nome_comercial válido
                if nome_comercial:
                    cursor.execute("""
                        UPDATE products 
                        SET nome_comercial = ?
                        WHERE id = ?
                    """, (nome_comercial, produto_id))
            
            conn.commit()

        return jsonify({
            "status": "success",
            "message": f"{len(produtos)} produtos atualizados com sucesso!"
        })
    except Exception as e:
        print(f"Erro ao salvar os dados da tabela: {e}")
        return jsonify({
            "status": "error",
            "message": "Erro ao salvar os dados da tabela."
        }), 500

# Rotas anteriores (custom_fields, produtos, etc.)

@app.route('/')
def index():
    """
    Página inicial do sistema.
    """
    return render_template('index.html')

if __name__ == '__main__':
    init_db()  # Inicializa o banco de dados
    app.run(debug=True)



# Imprimir todas as rotas registradas
print("Rotas registradas no Flask:")
print(app.url_map)

# Inicializa o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
