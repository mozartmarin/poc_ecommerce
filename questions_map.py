# questions_map.py

def get_question_map():
    return {
        "ticket_medio": {
            "exemplos": [
                "qual o ticket médio",
                "ticket médio por pedido",
                "média de valor por pedido"
            ],
            "descricao": "Ticket médio dos pedidos faturados",
            "funcao": "answer_ticket_medio"
        },
        "desconto_medio": {
            "exemplos": [
                "qual o desconto médio",
                "média de descontos",
                "desconto médio aplicado"
            ],
            "descricao": "Desconto médio nos pedidos faturados",
            "funcao": "answer_desconto_medio"
        },
        "top_produtos": {
            "exemplos": [
                "produtos mais vendidos",
                "top produtos",
                "itens mais vendidos"
            ],
            "descricao": "Produtos mais vendidos",
            "funcao": "top_produtos"
        },
        "formas_pgto": {
            "exemplos": [
                "formas de pagamento",
                "qual a forma de pagamento mais comum",
                "tipos de pagamento usados"
            ],
            "descricao": "Distribuição de formas de pagamento",
            "funcao": "formas_pagamento"
        },
        "frete_gratis": {
            "exemplos": [
                "quantos com frete grátis",
                "pedidos com frete gratis",
                "frete gratis foi aplicado"
            ],
            "descricao": "Total de pedidos com frete grátis",
            "funcao": "frete_gratis"
        },
        "status_pedidos": {
            "exemplos": [
                "status dos pedidos",
                "quantos pedidos faturados",
                "situação dos pedidos"
            ],
            "descricao": "Distribuição por status de pedidos",
            "funcao": "status_pedidos"
        },
        "tipo_cliente": {
            "exemplos": [
                "tipo de cliente",
                "cliente físico ou jurídico",
                "quantos são PJ"
            ],
            "descricao": "Distribuição por tipo de cliente",
            "funcao": "tipo_cliente"
        }
    }
