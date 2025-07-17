# app_correcao_final_2.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import base64
import requests
import json

# --- Configuração da Aplicação ---
app = Flask(__name__)
CORS(app)

# --- Chaves de API (MANTIDAS NO CÓDIGO) ---
API_KEY = "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"
GOOGLE_API_KEY = "AIzaSyCKqccRcYrhRJ01xg0VhzKB3-6stk4KpdY"
GOOGLE_CSE_ID = "546c42f0fe11e4ee4"

# --- Configuração do OpenAI Client ---
client = openai.OpenAI(api_key=API_KEY)

# --- Frontend HTML e JavaScript (sem alterações) ---
@app.route('/')
def home():
    # O frontend está estável e não precisa de mudanças.
    # Omitido para manter a resposta limpa.
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Meu Assessor Fashion</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }
            h1 { color: #333; text-align: center; }
            #chat { height: 450px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; background-color: #fff; border-radius: 8px; display: flex; flex-direction: column; }
            .message-container { display: flex; flex-direction: column; margin: 5px 0; }
            .message { padding: 10px 15px; border-radius: 15px; line-height: 1.6; max-width: 80%; word-wrap: break-word; }
            .user { background-color: #e1f5fe; align-self: flex-end; }
            .ai { background-color: #f1f8e9; align-self: flex-start; }
            .error { background-color: #ffebee; color: #c62828; align-self: stretch; text-align: center; }
            .info { background-color: #f5f5f5; color: #555; font-style: italic; align-self: stretch; text-align: center; }
            .input-container { display: flex; align-items: center; }
            #input { flex-grow: 1; padding: 12px; border: 1px solid #ccc; border-radius: 8px; }
            button { padding: 12px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; border-radius: 8px; margin-left: 10px; }
            #file-input { display: none; }
            .file-label { padding: 12px 20px; background: #2196F3; color: white; border: none; cursor: pointer; border-radius: 8px; text-align: center; }
            .file-preview { max-width: 150px; max-height: 150px; margin-top: 10px; border-radius: 8px; }
            #preview-container { text-align: center; margin-bottom: 10px; position: relative; display: inline-block; }
            .remove-btn { background: #ff4444; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; position: absolute; top: 5px; right: -5px; font-size: 14px; }
            a { color: #0066cc; font-weight: bold; }
            a:hover { text-decoration: underline; }
            .ai ul { padding-left: 20px; margin: 5px 0 0 0; }
            .ai li { margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <h1>Meu Assessor Fashion</h1>
        <div id="chat"></div>
        <div id="preview-wrapper" style="text-align: center;"><div id="preview-container"></div></div>
        <div class="input-container">
            <label for="file-input" class="file-label">📎 Imagem</label>
            <input id="file-input" type="file" accept="image/*">
            <input id="input" placeholder="Peça dicas ou envie uma imagem..." autofocus>
            <button onclick="sendMessage()">Enviar</button>
        </div>
        <script>
            let currentAttachment = null;
            let conversationHistory = [];
            function addMessage(role, content, id = null) {
                const chat = document.getElementById('chat');
                const container = document.createElement('div');
                container.className = 'message-container';
                const div = document.createElement('div');
                div.className = `message ${role}`;
                if (id) { div.id = id; }
                div.innerHTML = content;
                container.appendChild(div);
                chat.appendChild(container);
                chat.scrollTop = chat.scrollHeight;
                return div;
            }
            function updateMessage(id, newContent, newRole) {
                const messageDiv = document.getElementById(id);
                if (messageDiv) {
                    messageDiv.className = `message ${newRole}`;
                    messageDiv.innerHTML = newContent;
                }
            }
            document.getElementById('file-input').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (!file) return;
                currentAttachment = file;
                const previewContainer = document.getElementById('preview-container');
                previewContainer.innerHTML = '';
                const reader = new FileReader();
                reader.onload = function(event) {
                    const img = document.createElement('img');
                    img.src = event.target.result;
                    img.className = 'file-preview';
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-btn';
                    removeBtn.innerHTML = '×';
                    removeBtn.onclick = function() {
                        currentAttachment = null;
                        previewContainer.innerHTML = '';
                        document.getElementById('file-input').value = '';
                    };
                    previewContainer.appendChild(img);
                    previewContainer.appendChild(removeBtn);
                };
                reader.readAsDataURL(file);
            });
            async function sendMessage() {
                const input = document.getElementById('input');
                const message = input.value.trim();
                if (!message && !currentAttachment) {
                    alert("Por favor, digite uma pergunta ou envie uma imagem.");
                    return;
                }
                const userMessage = message || "Análise de imagem";
                addMessage('user', userMessage);
                conversationHistory.push({ "role": "user", "content": userMessage });
                input.disabled = true;
                document.querySelector('button').disabled = true;
                document.getElementById('file-input').disabled = true;
                const statusDiv = addMessage('info', 'Pensando...', 'status-message');
                try {
                    let response;
                    if (currentAttachment) {
                        const formData = new FormData();
                        formData.append('prompt', userMessage);
                        formData.append('file', currentAttachment);
                        formData.append('history', JSON.stringify(conversationHistory));
                        updateMessage('status-message', 'Analisando a imagem...', 'info');
                        const analyzeResponse = await fetch('/analyze-image', { method: 'POST', body: formData });
                        if (!analyzeResponse.ok) throw new Error((await analyzeResponse.json()).error);
                        const analysisData = await analyzeResponse.json();
                        const itemNames = (analysisData.clothing_items || []).map(item => `"${item.item}"`).join(', ');
                        if (!itemNames) {
                            updateMessage('status-message', 'Não consegui identificar itens de roupa na imagem. Tente outra foto ou pergunta.', 'ai');
                            conversationHistory.push({ "role": "assistant", "content": "Não consegui identificar itens de roupa na imagem." });
                            return; // Encerra o fluxo aqui
                        }
                        updateMessage('status-message', `Identifiquei: ${itemNames}.<br>Buscando os melhores links...`, 'info');
                        const findLinksResponse = await fetch('/find-links', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(analysisData)
                        });
                        if (!findLinksResponse.ok) throw new Error((await findLinksResponse.json()).error);
                        response = await findLinksResponse.json();
                    } else {
                        const textResponse = await fetch('/chat-text-only', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ history: conversationHistory })
                        });
                        if (!textResponse.ok) throw new Error((await textResponse.json()).error);
                        response = await textResponse.json();
                    }
                    updateMessage('status-message', response.response, 'ai');
                    conversationHistory.push({ "role": "assistant", "content": response.response });
                } catch (error) {
                    updateMessage('status-message', `<strong>Erro:</strong> ${error.message}`, 'error');
                    conversationHistory.pop();
                } finally {
                    input.disabled = false;
                    document.querySelector('button').disabled = false;
                    document.getElementById('file-input').disabled = false;
                    input.value = '';
                    document.getElementById('file-input').value = '';
                    currentAttachment = null;
                    document.getElementById('preview-container').innerHTML = '';
                    input.focus();
                }
            }
            document.getElementById('input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """

# --- Backend (com a correção na rota /analyze-image) ---

def get_clean_search_keywords(item_name):
    try:
        prompt = f"Beleza, meu parceiro! Agora, do item de moda masculino a seguir, preciso que você extraia APENAS as palavras-chave essenciais para uma busca de sucesso em e-commerce. Pense em tipo, cor, material e a característica principal. Item: \'{item_name}\'. Responda APENAS com as palavras-chave limpas, em minúsculas, focando no que realmente importa para o vestuário masculino. Sem enrolação, direto ao ponto."
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.0, max_tokens=20)
        keywords = response.choices[0].message.content.strip().replace('"', '')
        return keywords if keywords else item_name.lower()
    except Exception as e:
        print(f"Erro ao limpar keywords: {e}")
        return item_name.lower()

def google_search_for_item(keywords, gender="unissex", num=2):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID: return "<div>Chaves da API do Google não configuradas.</div>"
    trusted_sites = ["amazon.com.br", "mercadolivre.com.br", "renner.com.br", "cea.com.br", "dafiti.com.br", "zattini.com.br", "netshoes.com.br", "centauro.com.br", "riachuelo.com.br"]
    sites_query = " OR ".join([f"site:{site}" for site in trusted_sites])
    query = f"{keywords} {gender} {sites_query}"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "q": query, "num": num, "hl": "pt", "gl": "br", "safe": "active"}
    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=5 )
        resp.raise_for_status()
        data = resp.json()
        results = []
        if "items" in data and data["items"]:
            for item in data["items"]:
                title, link, snippet = item.get("title", "Link"), item.get("link"), item.get("snippet", "...")
                if link: results.append(f'<div><a href="{link}" target="_blank">{title}</a></div>')
            return "".join(results)
        return "<div>Nenhum link de compra relevante encontrado.</div>"
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar no Google: {e}")
        return "<div>Falha ao buscar links de compra.</div>"

def format_response_html(analysis):
    html_response = f"<p><b>Análise de Estilo:</b> {analysis.get('style_analysis', 'N/A')}</p><b>Peças e sugestões de compra:</b><br><br>"
    clothing_items = analysis.get('clothing_items', [])
    if clothing_items and isinstance(clothing_items, list):
        for item in clothing_items:
            html_response += f'<div><b>{item.get("item", "N/A").title()}</b><br>{item.get("shopping_links", "...")}</div><br>'
    fashion_tips = analysis.get('fashion_tips')
    if fashion_tips and isinstance(fashion_tips, list):
        html_response += "<b>Dicas de moda:</b><ul>"
        for tip in fashion_tips:
            html_response += f"<li>{tip}</li>"
        html_response += "</ul>"
    return html_response

# --- ROTA /analyze-image COM O PROMPT CORRIGIDO ---
@app.route('/analyze-image', methods=['POST'])
def analyze_image_handler():
    if 'file' not in request.files: return jsonify({"error": "Nenhum arquivo de imagem enviado."}), 400
    
    file = request.files['file']
    prompt_text = request.form.get('prompt', 'Analise este look para mim.')
    history_str = request.form.get('history', '[]')
    conversation_history = json.loads(history_str)
    
    image_data = base64.b64encode(file.read()).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{image_data}"
    
    # **CORREÇÃO APLICADA AQUI**
    # Restauramos o prompt detalhado, garantindo que a palavra "JSON" esteja presente.
    system_prompt = """
    Você é Felipe Titto, o consultor de imagem e estilo masculino que vai direto ao ponto. Com a minha vasta experiência em moda, comportamento e como a imagem impacta o sucesso, minha missão é te guiar para um estilo autêntico e impactante, alinhado aos seus objetivos pessoais e profissionais. Minha linguagem é direta, carismática e sempre focada em resultados. Pense como eu falaria, com a minha energia e confiança.

    Ao analisar a imagem de um look masculino, entregue uma análise completa e detalhada. Considere o contexto da nossa conversa e o perfil do usuário (se tivermos essa informação). Minha análise é sempre prática e acionável, focada exclusivamente na moda masculina e no que realmente funciona para você.

    Siga estritamente o seguinte formato de resposta JSON:
    {
    "style_analysis": "Faça uma análise concisa e inspiradora do estilo do look masculino, com a minha voz e perspectiva. Ex: \'Esse look é puro jogo de cintura! Casual, mas com uma pegada que mostra quem manda. A combinação de cores? Acertou em cheio, meu parceiro!\',",
    "clothing_items": [
        {\"item\": \'Nome específico da peça de roupa masculina (ex: \'camiseta de algodão egípcio preta\', \'bermuda de sarja cáqui\')\'}
    ],
    "fashion_tips": [
        "Dica prática e direta do Felipe Titto sobre como usar ou combinar as peças, ou sobre acessórios que eu mesmo usaria para elevar o nível do look. Ex: \'Pra dar um upgrade, joga um tênis branco de couro e um óculos de sol com armação mais robusta. Faz toda a diferença, pode apostar!\',",
        "Outra dica de estilo ou posicionamento, com a minha personalidade. Ex: \'Lembre-se: a confiança não se compra, se constrói. E a sua imagem é uma ferramenta poderosa nessa construção. Vista-se para o sucesso, mas sempre com a sua verdade, sem mimimi.\'"
    ]
    }
    A chave "fashion_tips" DEVE ser uma lista de strings, com dicas que reflitam a minha filosofia de estilo e posicionamento. Mantenha o foco em moda masculina e em como a imagem impacta o mundo profissional e pessoal do homem. Use uma linguagem que me represente, com termos como \'meu parceiro\', \'pode apostar\', \'sem mimimi\', quando apropriado.
    """
    messages = conversation_history[:-1]
    messages.insert(0, {"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": [{"type": "text", "text": prompt_text}, {"type": "image_url", "image_url": {"url": image_url}}]})

    try:
        response = client.chat.completions.create(model="gpt-4o", response_format={"type": "json_object"}, messages=messages, max_tokens=1500)
        analysis_result = json.loads(response.choices[0].message.content)
        return jsonify(analysis_result)
    except Exception as e:
        print(f"Erro detalhado na análise da IA: {e}")
        return jsonify({"error": f"Erro na análise da IA: {str(e)}"}), 500

@app.route('/find-links', methods=['POST'])
def find_links_handler():
    try:
        analysis_data = request.get_json()
        gender = analysis_data.get("gender", "unissex")
        clothing_items = analysis_data.get('clothing_items', [])
        if clothing_items and isinstance(clothing_items, list):
            for item in clothing_items:
                clean_keywords = get_clean_search_keywords(item.get('item', ''))
                item['shopping_links'] = google_search_for_item(clean_keywords, gender)
        final_html = format_response_html(analysis_data)
        return jsonify({"response": final_html})
    except Exception as e:
        return jsonify({"error": f"Erro ao processar os links: {str(e)}"}), 500

@app.route('/chat-text-only', methods=['POST'])
def chat_text_handler():
    try:
        data = request.get_json()
        conversation_history = data.get('history', [])
        if not conversation_history:
            return jsonify({"error": "Histórico da conversa está vazio."}), 400

        intent_analysis_prompt = f"""
        Felipe Titto aqui. Analise o histórico da nossa conversa com o usuário. Qual é a real intenção da ÚLTIMA mensagem dele? É crucial que você identifique isso com precisão, sempre com o foco total em moda e estilo masculino. O objetivo é ser cirúrgico na resposta.
        Responda em JSON. As intenções possíveis são: "get_fashion_advice" (para conselhos de estilo) ou "find_shopping_links" (para links de compra).
        - Se a intenção for "find_shopping_links", extraia da conversa uma lista de termos de busca para e-commerce na chave "search_queries". Priorize os termos mais relevantes para o vestuário masculino, aqueles que realmente trarão resultados na busca.
        - Se for "get_fashion_advice", a chave "search_queries" deve ser uma lista vazia. Sem desculpas, preciso da intenção clara.
        
        Histórico da Conversa: {json.dumps(conversation_history, indent=2)}
        """
        
        intent_response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": intent_analysis_prompt}],
            temperature=0.1
        )
        intent_data = json.loads(intent_response.choices[0].message.content)
        intent = intent_data.get("intent")

        if intent == "find_shopping_links":
            search_queries = intent_data.get("search_queries", [])
            if not search_queries:
                return jsonify({"response": "Entendi que você quer links, mas não consegui identificar exatamente do quê. Pode especificar os itens que deseja comprar?"})

            links_html = ""
            for query in search_queries:
                gender_context = "masculino" if "masculino" in query else "feminino" if "feminino" in query else "unissex"
                links_html += f"<b>Buscas para '{query}':</b><br>"
                links_html += google_search_for_item(query, gender=gender_context) + "<br>"
            
            final_response = f"<p>Com certeza! Encontrei alguns links com base no nosso papo:</p>{links_html}"
            return jsonify({"response": final_response})

        else: # A intenção é "get_fashion_advice"
            advice_prompt = """
            Felipe Titto na área! Sua missão é entregar um conselho de imagem e estilo masculino que realmente faça a diferença. Responda à última pergunta do usuário de forma clara, útil e com a minha energia e personalidade. Use todo o histórico da nossa conversa para dar o contexto certo. Meu foco é sempre empoderar o homem a se vestir melhor, a se posicionar com confiança e a dominar o jogo da imagem. Pense em como eu falaria, com a minha paixão por resultados e autenticidade. Use frases como \'meu parceiro\', \'pode apostar\', \'sem mimimi\', \'é jogo de cintura\', \'direto ao ponto\', \'faz toda a diferença\', quando for natural.
            Use formatação HTML simples (<b>, <ul>, <li>). Para links, use a tag <a>, por exemplo: <a href=\'URL\'>Texto do Link</a>. NÃO use Markdown. E nada de enrolação, ok? Seja direto e impactante.
            """
            messages = [{"role": "system", "content": advice_prompt}] + conversation_history
            
            advice_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            content = advice_response.choices[0].message.content
            return jsonify({"response": content})

    except Exception as e:
        print(f"Erro no chat de texto: {e}")
        return jsonify({"error": f"Ocorreu um erro ao processar sua pergunta: {str(e)}"}), 500

# --- Execução da Aplicação ---
if __name__ == '__main__':
    app.run(port=5001, debug=True)
