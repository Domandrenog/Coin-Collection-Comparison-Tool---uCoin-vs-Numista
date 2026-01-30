#!/usr/bin/env python3
"""
Script para comparar moedas e quantidades entre ficheiros Excel (ucoin.xlsx e numista.xls)
"""

import sys
from datetime import datetime

import pandas as pd


def carregar_excel(ficheiro):
    """Carrega o ficheiro Excel e retorna um DataFrame"""
    try:
        if ficheiro.endswith(".xlsx"):
            df = pd.read_excel(ficheiro, engine="openpyxl")
        else:
            df = pd.read_excel(ficheiro)
        return df
    except Exception as e:
        print(f"Erro ao carregar {ficheiro}: {e}")
        sys.exit(1)


def criar_chave_moeda(row, tipo):
    """Cria uma chave única para cada moeda baseada em múltiplos campos"""
    try:
        if tipo == "ucoin":
            # Usar: País, Ano, Denominação, Número (referência KM)
            pais = str(row.get("país", "")).strip()
            ano = str(row.get("ano", "")).strip()
            denom = str(row.get("denominação", "")).strip()
            ref = str(row.get("número", "")).strip()
            return f"{pais}|{ano}|{denom}|{ref}"
        else:  # numista
            # Usar: Emissor, Ano, Título, Referência
            emissor = str(row.get("emissor", "")).strip()
            ano = str(row.get("ano", "")).strip()
            titulo = str(row.get("título", "")).strip()
            ref = str(row.get("referência", "")).strip()
            return f"{emissor}|{ano}|{titulo}|{ref}"
    except:
        return None


def normalizar_para_comparacao(s):
    """Normaliza string para comparação (remove acentos, maiúsculas, etc)"""
    if pd.isna(s):
        return ""
    s = str(s).lower().strip()
    # Remover caracteres especiais
    s = s.replace("ã", "a").replace("á", "a").replace("à", "a")
    s = s.replace("é", "e").replace("ê", "e")
    s = s.replace("í", "i")
    s = s.replace("ó", "o").replace("õ", "o").replace("ô", "o")
    s = s.replace("ú", "u").replace("ü", "u")
    s = s.replace("ç", "c")

    # Normalizar variações comuns de nomes de países
    if "united states" in s or "estados unidos" in s or s == "usa":
        return "usa"
    if "soviet union" in s or "uniao sovietica" in s or s == "ussr" or s == "urss":
        return "ussr"

    return s


def normalizar_referencia(ref):
    """Normaliza referência de catálogo para comparação"""
    if pd.isna(ref):
        return ""
    ref = str(ref).strip().upper()
    # Remover espaços e normalizar separadores
    ref = ref.replace(" ", "")
    # Remover letras variantes que podem aparecer (e.g., KM# A192 -> KM#192)
    # Mas manter letras no final (e.g., KM# 164a)
    import re

    # Match pattern like KM# A123 and convert to KM#123
    ref = re.sub(r"(KM#|Y#)\s*A(\d+)", r"\1\2", ref)
    return ref


def extrair_numeros(texto):
    """Extrai apenas os números de um texto"""
    if pd.isna(texto):
        return ""
    import re

    numeros = re.findall(r"\d+\.?\d*", str(texto))
    return "".join(numeros)


def extrair_diametro(diametro_str):
    """Extrai o valor numérico do diâmetro"""
    if pd.isna(diametro_str):
        return None
    import re

    match = re.search(r"(\d+\.?\d*)", str(diametro_str))
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


def tentar_match_aproximado(df1, df2):
    """
    Matching usando critérios obrigatórios:
    1. País/Emissor deve ser igual
    2. Ano deve ser igual
    3. Diâmetro deve ser igual (com tolerância de ±0.5mm)
    4. Valor da moeda comparado por números apenas
    """
    matches = []
    matched_idx2 = set()

    for idx1, row1 in df1.iterrows():
        melhor_score = 0
        melhor_idx2 = None

        # Critérios obrigatórios do uCoin
        pais1 = normalizar_para_comparacao(row1.get("país", ""))
        ano1_raw = row1.get("ano", "")

        # Para moedas de Espanha, o ano real pode estar na coluna var. (ano dentro da estrela)
        # O ano correto é "19" + var. (ex: var. = 77 → ano = 1977)
        var1 = row1.get("var.", "")
        if pd.notna(var1) and pais1 and "espanha" in pais1:
            try:
                var_num = int(float(str(var1).strip()))
                ano1 = 1900 + var_num
            except:
                # Se var. não for válido, usar o ano normal
                try:
                    ano1 = (
                        int(float(str(ano1_raw).strip()))
                        if pd.notna(ano1_raw)
                        else None
                    )
                except:
                    ano1 = None
        else:
            # Para outras moedas, usar o ano normal
            try:
                ano1 = int(float(str(ano1_raw).strip())) if pd.notna(ano1_raw) else None
            except:
                ano1 = None

        diametro1 = extrair_diametro(row1.get("diametro, mm", ""))
        valor1_num = extrair_numeros(row1.get("denominação", ""))

        # Pular se faltar informação essencial
        if not pais1 or not ano1:
            continue

        for idx2, row2 in df2.iterrows():
            if idx2 in matched_idx2:  # Evitar duplicados
                continue

            # Critérios obrigatórios do Numista (usar 'diâmetro' em vez de 'diametro, mm')
            emissor2 = normalizar_para_comparacao(row2.get("emissor", ""))
            pais2 = normalizar_para_comparacao(row2.get("país", ""))

            # Tentar ambos os anos: "ano" e "ano gregoriano"
            ano_normal = row2.get("ano", "")
            ano_gregoriano = row2.get("ano gregoriano", "")

            ano2 = None
            ano2_alt = None  # Ano alternativo para verificação

            # Extrair "ano"
            if (
                pd.notna(ano_normal)
                and str(ano_normal).strip()
                and str(ano_normal).strip() != "nan"
            ):
                try:
                    ano2 = int(float(str(ano_normal).strip()))
                except:
                    pass

            # Extrair "ano gregoriano"
            if (
                pd.notna(ano_gregoriano)
                and str(ano_gregoriano).strip()
                and str(ano_gregoriano).strip() != "nan"
            ):
                try:
                    ano2_alt = int(float(str(ano_gregoriano).strip()))
                except:
                    pass

            # Se não temos ano2, usar o alternativo
            if ano2 is None:
                ano2 = ano2_alt
                ano2_alt = None

            diametro2 = extrair_diametro(row2.get("diâmetro", ""))
            valor2_num = extrair_numeros(row2.get("valor de face", ""))

            # Normalizar valores para comparação (converter decimais para inteiros se possível)
            # Ex: "0.05" -> "5" (5 centavos), "0.5" -> "50" (50 centavos), "1.0" -> "1"
            if valor2_num:
                try:
                    val_float = float(valor2_num)
                    if val_float < 1.0:
                        # É centavos/céntimos - multiplicar por 100
                        valor2_num = str(int(val_float * 100))
                    else:
                        # É unidade inteira
                        valor2_num = str(int(val_float))
                except:
                    pass

            # CRITÉRIOS OBRIGATÓRIOS

            # 1. País deve ser igual (com flexibilidade para variações de nome)
            pais_match = False
            if pais1 and (emissor2 or pais2):
                # Match exato
                if pais1 == emissor2 or pais1 == pais2:
                    pais_match = True
                # Match se um contém o outro (qualquer direção)
                elif emissor2 and (pais1 in emissor2 or emissor2 in pais1):
                    pais_match = True
                elif pais2 and (pais1 in pais2 or pais2 in pais1):
                    pais_match = True

            if not pais_match:
                continue  # OBRIGATÓRIO

            # 2. Ano deve ser igual (considerar tanto "ano" quanto "ano gregoriano")
            ano_match = False
            if ano1 == ano2:
                ano_match = True
            elif ano2_alt is not None and ano1 == ano2_alt:
                ano_match = True

            if not ano_match:
                continue  # OBRIGATÓRIO

            # 3. Calcular diferença de diâmetro (se ambos disponíveis)
            dif_diametro = None
            if diametro1 is not None and diametro2 is not None:
                dif_diametro = abs(diametro1 - diametro2)

            # Se chegou aqui, passou nos critérios obrigatórios (país + ano)
            score = 100  # Base score para critérios obrigatórios

            # Bonus/penalidade por diâmetro
            if dif_diametro is not None:
                if dif_diametro <= 0.5:
                    score += 100  # Diâmetro quase igual - PESO MUITO ALTO
                elif dif_diametro <= 1.0:
                    score += 70  # Diâmetro próximo
                elif dif_diametro <= 2.0:
                    score += 40  # Diâmetro aceitável
                elif dif_diametro <= 3.5:
                    score += 10  # Diâmetro razoável
                else:
                    # Diâmetro muito diferente - grande penalidade
                    score -= 100  # Penalidade forte

            # 4. Comparar valor (apenas números) - PESO ALTO
            if valor1_num and valor2_num:
                if valor1_num == valor2_num:
                    score += 150  # Match perfeito do valor
                elif valor1_num in valor2_num or valor2_num in valor1_num:
                    score += 50  # Match parcial
            elif not valor1_num and not valor2_num:
                # Ambos sem valor numérico (raro mas possível)
                score += 80

            # 5. Comparar referência de catálogo (se disponível)
            ref1 = normalizar_referencia(row1.get("número", ""))
            ref2 = normalizar_referencia(row2.get("referência", ""))
            if ref1 and ref2:
                if ref1 == ref2:
                    score += 200  # Match perfeito de referência - PESO MUITO ALTO
                elif ref1 in ref2 or ref2 in ref1:
                    score += 80  # Match parcial de referência

            if score > melhor_score:
                melhor_score = score
                melhor_idx2 = idx2

        if melhor_idx2 is not None:
            matches.append(
                {"idx_ucoin": idx1, "idx_numista": melhor_idx2, "score": melhor_score}
            )
            matched_idx2.add(melhor_idx2)

    return matches


def agrupar_moedas_duplicadas(df, tipo):
    """Agrupa moedas idênticas e soma as quantidades"""
    if tipo == "ucoin":
        # IMPORTANTE: Ajustar o ano baseado na coluna var. ANTES de agrupar
        # Para moedas de Espanha, var. representa o ano dentro da estrela
        df = df.copy()
        if "var." in df.columns:
            for idx, row in df.iterrows():
                pais = normalizar_para_comparacao(row.get("país", ""))
                var_val = row.get("var.", "")
                if pd.notna(var_val) and pais and "espanha" in pais:
                    try:
                        var_num = int(float(str(var_val).strip()))
                        # Ano real é 1900 + var. (ex: var. 77 → 1977)
                        df.at[idx, "ano"] = 1900 + var_num
                    except:
                        pass

        # Identificar colunas principais para agrupamento
        cols_chave = ["país", "ano", "denominação", "diâmetro", "número"]
        cols_chave = [c for c in cols_chave if c in df.columns]

        # Agrupar e somar quantidades
        df_agrupado = df.groupby(cols_chave, dropna=False, as_index=False).agg(
            {"quantidade": "sum"}
        )

        # Adicionar outras colunas que possam existir (pegar primeiro valor)
        for col in df.columns:
            if col not in cols_chave and col != "quantidade":
                df_temp = df.groupby(cols_chave, dropna=False, as_index=False)[
                    col
                ].first()
                df_agrupado = df_agrupado.merge(df_temp, on=cols_chave, how="left")

        return df_agrupado
    else:  # numista
        # Identificar colunas principais para agrupamento
        cols_chave = [
            "emissor",
            "ano",
            "ano gregoriano",
            "título",
            "diâmetro",
            "referência",
        ]
        cols_chave = [c for c in cols_chave if c in df.columns]

        # Agrupar e somar quantidades
        df_agrupado = df.groupby(cols_chave, dropna=False, as_index=False).agg(
            {"quantidade": "sum"}
        )

        # Adicionar outras colunas que possam existir (pegar primeiro valor)
        for col in df.columns:
            if col not in cols_chave and col != "quantidade":
                df_temp = df.groupby(cols_chave, dropna=False, as_index=False)[
                    col
                ].first()
                df_agrupado = df_agrupado.merge(df_temp, on=cols_chave, how="left")

        return df_agrupado


def comparar_moedas(df1, df2, nome1, nome2):
    """Compara dois DataFrames de moedas"""
    print(f"\n{'='*80}")
    print(f"COMPARAÇÃO ENTRE {nome1.upper()} E {nome2.upper()}")
    print(f"{'='*80}\n")

    # Normalizar nomes de colunas
    df1.columns = df1.columns.str.strip().str.lower()
    df2.columns = df2.columns.str.strip().str.lower()

    # Mostrar informação básica ANTES de agrupar
    print(f"📊 {nome1} (original):")
    print(f"   - Total de linhas: {len(df1)}")
    qtd_total_1_original = df1["quantidade"].sum() if "quantidade" in df1.columns else 0
    print(f"   - Quantidade total: {int(qtd_total_1_original)} moedas\n")

    print(f"📊 {nome2} (original):")
    print(f"   - Total de linhas: {len(df2)}")
    qtd_total_2_original = df2["quantidade"].sum() if "quantidade" in df2.columns else 0
    print(f"   - Quantidade total: {int(qtd_total_2_original)} moedas\n")

    # Agrupar moedas duplicadas
    print("🔄 A agrupar moedas duplicadas...")
    df1_original_len = len(df1)
    df2_original_len = len(df2)

    df1 = agrupar_moedas_duplicadas(df1, "ucoin")
    df2 = agrupar_moedas_duplicadas(df2, "numista")

    duplicatas_1 = df1_original_len - len(df1)
    duplicatas_2 = df2_original_len - len(df2)

    if duplicatas_1 > 0:
        print(f"   ✓ {nome1}: {duplicatas_1} linhas duplicadas foram agrupadas")
    if duplicatas_2 > 0:
        print(f"   ✓ {nome2}: {duplicatas_2} linhas duplicadas foram agrupadas")
    print()

    # Mostrar informação básica DEPOIS de agrupar
    print(f"📊 {nome1} (agrupado):")
    print(f"   - Total de linhas: {len(df1)}")
    print(
        f"   - Colunas principais: país, ano, denominação, quantidade, número (referência)\n"
    )

    print(f"📊 {nome2}:")
    print(f"   - Total de linhas: {len(df2)}")
    print(f"   - Colunas principais: emissor, ano, título, quantidade, referência\n")

    # Estatísticas gerais
    qtd_total_1 = df1["quantidade"].sum() if "quantidade" in df1.columns else 0
    qtd_total_2 = df2["quantidade"].sum() if "quantidade" in df2.columns else 0

    print(f"📈 Quantidades totais:")
    print(f"   - {nome1}: {int(qtd_total_1)} moedas")
    print(f"   - {nome2}: {int(qtd_total_2)} moedas")
    print(f"   - Diferença: {int(qtd_total_1 - qtd_total_2)} moedas\n")

    # Fazer matching aproximado
    print("🔄 A fazer matching entre os ficheiros (isto pode demorar)...")
    matches = tentar_match_aproximado(df1, df2)

    matched_idx1 = {m["idx_ucoin"] for m in matches}
    matched_idx2 = {m["idx_numista"] for m in matches}

    print(f"✅ Encontradas {len(matches)} correspondências entre os ficheiros\n")

    # Moedas não correspondidas
    nao_match_ucoin = df1[~df1.index.isin(matched_idx1)]
    nao_match_numista = df2[~df2.index.isin(matched_idx2)]

    print(f"\n{'='*80}")
    print("MOEDAS NÃO CORRESPONDIDAS")
    print(f"{'='*80}\n")

    print(f"🔴 Apenas em {nome1}: {len(nao_match_ucoin)} moedas")
    print(f"🔴 Apenas em {nome2}: {len(nao_match_numista)} moedas\n")

    # Comparar quantidades das moedas correspondidas
    print(f"{'='*80}")
    print("COMPARAÇÃO DE QUANTIDADES (MOEDAS CORRESPONDIDAS)")
    print(f"{'='*80}\n")

    diferencas = []
    qtd_iguais = 0

    for match in matches:
        idx1 = match["idx_ucoin"]
        idx2 = match["idx_numista"]

        row1 = df1.loc[idx1]
        row2 = df2.loc[idx2]

        qtd1 = row1.get("quantidade", 0)
        qtd2 = row2.get("quantidade", 0)

        if qtd1 != qtd2:
            diferencas.append(
                {
                    "país/emissor": row1.get("país", ""),
                    "ano": row1.get("ano", ""),
                    "denominação": row1.get("denominação", ""),
                    "ref_ucoin": row1.get("número", ""),
                    "ref_numista": row2.get("referência", ""),
                    "qtd_ucoin": int(qtd1) if pd.notna(qtd1) else 0,
                    "qtd_numista": int(qtd2) if pd.notna(qtd2) else 0,
                    "diferença": (
                        int(qtd1 - qtd2) if pd.notna(qtd1) and pd.notna(qtd2) else 0
                    ),
                }
            )
        else:
            qtd_iguais += 1

    if diferencas:
        print(f"⚠️  Diferenças de quantidade: {len(diferencas)}")
        print(f"✅ Quantidades iguais: {qtd_iguais}\n")

        df_dif = pd.DataFrame(diferencas)
        print(df_dif.to_string(index=False))

        # Exportar para Excel
        nome_ficheiro = f"diferencas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df_dif.to_excel(nome_ficheiro, index=False)
        print(f"\n💾 Diferenças guardadas em: {nome_ficheiro}")
    else:
        print(
            f"✅ Todas as {len(matches)} moedas correspondidas têm quantidades iguais!"
        )

    # Analisar a diferença de 2 moedas
    print(f"\n{'='*80}")
    print("ANÁLISE DETALHADA DA DIFERENÇA DE 2 MOEDAS")
    print(f"{'='*80}\n")

    # Calcular contribuições para a diferença total
    qtd_nao_match_ucoin = (
        nao_match_ucoin["quantidade"].sum() if len(nao_match_ucoin) > 0 else 0
    )
    qtd_nao_match_numista = (
        nao_match_numista["quantidade"].sum() if len(nao_match_numista) > 0 else 0
    )

    # Diferenças nas moedas correspondidas
    dif_positivas = sum(d["diferença"] for d in diferencas if d["diferença"] > 0)
    dif_negativas = sum(d["diferença"] for d in diferencas if d["diferença"] < 0)

    print("📊 Contribuições para a diferença total:\n")
    print(f"   Moedas não correspondidas:")
    print(
        f"     • Apenas em uCoin: +{int(qtd_nao_match_ucoin)} moedas ({len(nao_match_ucoin)} tipos)"
    )
    print(
        f"     • Apenas em Numista: {int(qtd_nao_match_numista)} moedas ({len(nao_match_numista)} tipos)"
    )
    print(f"     • Sub-total: {int(qtd_nao_match_ucoin - qtd_nao_match_numista)}\n")

    print(f"   Moedas correspondidas com diferenças:")
    print(f"     • Mais em uCoin: +{int(dif_positivas)} moedas")
    print(f"     • Mais em Numista: {int(dif_negativas)} moedas")
    print(f"     • Sub-total: {int(dif_positivas + dif_negativas)}\n")

    total_final = int(
        qtd_nao_match_ucoin - qtd_nao_match_numista + dif_positivas + dif_negativas
    )
    print(f"   🎯 TOTAL: {total_final} moedas a mais em uCoin\n")

    print(f"{'='*80}")
    print("AS 2 MOEDAS QUE FALTAM")
    print(f"{'='*80}\n")

    # Se a diferença for das moedas correspondidas
    if abs(dif_positivas + dif_negativas) <= 5:
        print(
            "🔍 A diferença de 2 moedas vem das quantidades diferentes nas moedas correspondidas:\n"
        )
        moedas_relevantes = sorted(
            diferencas, key=lambda x: abs(x["diferença"]), reverse=True
        )[:10]
        df_rel = pd.DataFrame(moedas_relevantes)
        print(
            df_rel[
                [
                    "país/emissor",
                    "ano",
                    "denominação",
                    "ref_ucoin",
                    "qtd_ucoin",
                    "qtd_numista",
                    "diferença",
                ]
            ].to_string(index=False)
        )

    # Listar todas as diferenças positivas (moedas que faltam em numista)
    moedas_faltam_numista = [d for d in diferencas if d["diferença"] > 0]
    moedas_sobram_numista = [d for d in diferencas if d["diferença"] < 0]

    print(f"\n\n📋 RESUMO COMPLETO:\n")
    print(
        f"   • {len(moedas_faltam_numista)} tipos de moedas com mais quantidade em uCoin (+{int(dif_positivas)} unidades)"
    )
    print(
        f"   • {len(moedas_sobram_numista)} tipos de moedas com mais quantidade em Numista ({int(dif_negativas)} unidades)"
    )
    print(f"   • Saldo líquido: {int(dif_positivas + dif_negativas)} moedas")

    if moedas_faltam_numista:
        # Salvar apenas as que faltam
        nome_ficheiro_faltam = (
            f"faltam_em_numista_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        df_faltam = pd.DataFrame(moedas_faltam_numista)
        df_faltam.to_excel(nome_ficheiro_faltam, index=False)
        print(f"\n💾 Moedas com mais quantidade em uCoin: {nome_ficheiro_faltam}")

    # Exportar moedas não correspondidas
    if len(nao_match_ucoin) > 0 or len(nao_match_numista) > 0:
        nome_ficheiro2 = (
            f"nao_correspondidas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        with pd.ExcelWriter(nome_ficheiro2) as writer:
            if len(nao_match_ucoin) > 0:
                nao_match_ucoin[
                    ["país", "ano", "denominação", "número", "quantidade"]
                ].to_excel(writer, sheet_name="Apenas_uCoin", index=False)
            if len(nao_match_numista) > 0:
                nao_match_numista[
                    ["emissor", "ano", "título", "referência", "quantidade"]
                ].to_excel(writer, sheet_name="Apenas_Numista", index=False)
        print(f"💾 Moedas não correspondidas guardadas em: {nome_ficheiro2}")


def main():
    ficheiro1 = "ucoin.xlsx"
    ficheiro2 = "numista.xlsx"  # Atualizado para .xlsx

    print("🔄 A carregar ficheiros Excel...")

    # Carregar ficheiros
    df_ucoin = carregar_excel(ficheiro1)
    df_numista = carregar_excel(ficheiro2)

    # Comparar
    comparar_moedas(df_ucoin, df_numista, "ucoin", "numista")

    print("\n" + "=" * 80)
    print("✅ Comparação concluída!")
    print("=" * 80)


if __name__ == "__main__":
    main()
