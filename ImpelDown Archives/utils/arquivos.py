import json
import sqlite3

def exportar_ficha_markdown(caminho, dados):
    bounty_str = dados.get('recompensa', '0') + " Berries" if dados.get('recompensa') else "0 Berries"
    
    md = f"# {dados.get('nome', 'Inimigo')}\n"
    md += f"Nível: {dados.get('nivel', '1')} | Recompensa: {bounty_str}\n"
    md += f"PV: {dados.get('pv', 0)} | PE: {dados.get('pe', 0)}\n\n"
    md += "## Atributos\n"
    md += f"- Físico: {dados.get('fis', 0)} | Agilidade: {dados.get('agi', 0)} | Intelecto: {dados.get('int', 0)} | Instinto: {dados.get('inst', 0)}\n"
    md += f"- Grau Luta: {dados.get('luta', 0)} | Grau Acro: {dados.get('acro', 0)}\n\n"
    md += "## Loot e Drops\n" + dados.get('loot', '') + "\n\n"
    md += "## Habilidades\n"
    for hab in dados.get('habilidades', []):
        md += f"### {hab.get('titulo', 'Habilidade')}\n"
        md += f"Custo: {hab.get('custo', '-')} | Limite: {hab.get('limite', '-')} | Execução: {hab.get('execucao', '-')} | Alcance: {hab.get('alcance', '-')}\n"
        md += f"{hab.get('conteudo', '')}\n\n"
    md += "## Notas e História\n" + dados.get('historia', '')
    
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(md)

def exportar_ficha_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def importar_ficha_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_banco_sqlite(caminho_db, estrutura_arvore, dados_banco):
    conn = sqlite3.connect(caminho_db)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS dados_rpg (id INTEGER PRIMARY KEY, estrutura TEXT, fichas TEXT)')
    c.execute('DELETE FROM dados_rpg')
    c.execute('INSERT INTO dados_rpg (id, estrutura, fichas) VALUES (1, ?, ?)', 
              (json.dumps(estrutura_arvore), json.dumps(dados_banco)))
    conn.commit()
    conn.close()

def carregar_banco_sqlite(caminho_db):
    conn = sqlite3.connect(caminho_db)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS dados_rpg (id INTEGER PRIMARY KEY, estrutura TEXT, fichas TEXT)')
    c.execute('SELECT estrutura, fichas FROM dados_rpg WHERE id=1')
    row = c.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0]), json.loads(row[1])
    return None, None