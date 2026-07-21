import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# WEBページのタイトルと設定
st.set_page_config(page_title="取引所CFDコバンザメ投資計画", page_icon="🦅", layout="centered")

st.title("🦅 取引所CFDコバンザメ投資計画")
st.subheader("〜20万円少額テスト版・安全装置強化モード〜")
st.markdown("---")

# ⏰ 現在の時刻から「昼モード」「夜モード」を自動判定、または手動切り替え
current_hour = datetime.now().hour
default_mode = "🌙 夜間ハント（16:30〜深夜）" if (current_hour >= 16 or current_hour < 4) else "☀️ 日中ハント（朝8:30〜16:30）"

st.sidebar.markdown("### ⚙️ モード設定")
mode = st.sidebar.radio("実行する時間帯を選択してください", ["☀️ 日中ハント（朝8:30〜16:30）", "🌙 夜間ハント（16:30〜深夜）"], index=0 if default_mode.startswith("☀️") else 1)

# 起動ボタンの設置
if st.button(f"🔄 {mode[:2]} 最新データを解析して作戦を立案", type="primary"):
    with st.spinner("市場データを多角分析中..."):
        
        # --- 🚨 データ取り込み＆警告（安全装置）システム ---
        error_triggered = False
        error_message = ""
        
        try:
            # 各データの取得を試みる
            vix_data = yf.download("^VIX", period="3mo")
            n225_data = yf.download("^N225", period="3mo")
            cme_data = yf.download("NIY=F", period="2d")
            
            # 【チェック1】そもそもデータが空っぽ（通信障害や仕様変更）になっていないか
            if vix_data.empty or n225_data.empty or cme_data.empty:
                error_triggered = True
                missing = []
                if vix_data.empty: missing.append("VIX(恐怖指数)")
                if n225_data.empty: missing.append("日経平均")
                if cme_data.empty: missing.append("CME日経先物")
                error_message = f"データ配信元から一部のデータ（{ '、'.join(missing) }）を正常に取得できませんでした。配信元の仕様変更、またはシステム障害の可能性があります。"
            
        except Exception as e:
            # 【チェック2】通信エラーや予期せぬプログラム停止のキャッチ
            error_triggered = True
            error_message = f"通信エラーまたは予期せぬエラーが発生しました。インターネット接続を確認してください。（詳細エラー: {e}）"

        # もしデータ取り込みに異常があれば、ここで大警告を出して安全にストップ
        if error_triggered:
            st.error("🛑 【システム警告：作戦立案不能】")
            st.danger_box = st.markdown(
                f"""
                <div style="background-color:#ffe6e6; padding:20px; border-radius:10px; border: 2px solid #ff3333;">
                    <p style="color:#cc0000; font-weight:bold; margin-top:0;">⚠️ データの取り込みに失敗しました</p>
                    <p style="color:#333; font-size:14px;">{error_message}</p>
                    <p style="color:#666; font-size:12px; margin-bottom:0;">※古いデータで誤った指値を計算するのを防ぐため、処理を安全に中断しました。しばらく時間を置いてから再度お試しください。</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.stop() # ここでプログラムを強制停止（誤った作戦を出させない）

        # --- 正常時のデータ整形（二重構造を平らに直す） ---
        for df in [vix_data, n225_data, cme_data]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        # テクニカル指標の計算（日経平均）
        n225_data['MA25'] = n225_data['Close'].rolling(window=25).mean()
        n225_data['Kairi'] = ((n225_data['Close'] - n225_data['MA25']) / n225_data['MA25']) * 100

        delta = n225_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        n225_data['RSI'] = 100 - (100 / (1 + rs))

        # 最新値の抽出
        prev_vix = float(vix_data['Close'].iloc[-1])
        prev_n225_close = float(n225_data['Close'].iloc[-1])
        latest_cme = float(cme_data['Close'].iloc[-1])
        
        latest_kairi = float(n225_data['Kairi'].iloc[-1])
        latest_rsi = float(n225_data['RSI'].iloc[-1])

        cme_diff = latest_cme - prev_n225_close
        diff_sign = "+" if cme_diff >= 0 else ""

        # --- 表示部分 ---
        st.subheader("📊 現在の市場ステータス")
        col1, col2, col3 = st.columns(3)
        col1.metric("日経平均（終値）", f"{prev_n225_close:,.0f} 円")
        col2.metric("CME日経先物", f"{latest_cme:,.0f} 円", f"{diff_sign}{cme_diff:,.0f} 円")
        col3.metric("VIX（恐怖指数）", f"{prev_vix:.2f}")

        st.markdown("**🔍 テクニカル指標**")
        col4, col5 = st.columns(2)
        col4.metric("25日線 乖離率", f"{latest_kairi:.2f} %")
        col5.metric("RSI（14日）", f"{latest_rsi:.1f} %")
        st.markdown("---")

        st.subheader(f"⚔️ {mode[:2]} 本日の作戦指示")

        # ==================== ☀️ 日中ハントモードのロジック ====================
        if "☀️" in mode:
            if prev_vix >= 25 or latest_kairi <= -5.0:
                st.error("🚨 レベル3：【大パニック・絶好のハント機会】")
                target_limit = np.floor(prev_n225_close * (1 - 0.027))
                st.info(f"**💡 買い指値価格: {target_limit:,.0f} 円**（マイクロ1枚・当日限り）")
                st.caption("利確目標: +500円幅")
            elif latest_rsi <= 35.0 or latest_kairi <= -3.0:
                st.warning("⚠️ レベル2：【テクニカル売られすぎ・チャンス拡大】")
                target_limit = np.floor(prev_n225_close * (1 - 0.015))
                st.info(f"**💡 買い指値価格: {target_limit:,.0f} 円**（マイクロ1枚・当日限り）")
                st.caption("利確目標: +300円〜400円幅（早めの逃げを意識）")
            else:
                st.success("💤 レベル1：【市場は平穏・冬眠推奨】")
                st.write("日中は仕掛ける基準に達していません。夜間ハントの動きを待ちましょう。")
                fc_limit = np.floor(prev_n225_close - 1500)
                st.caption(f"※どうしても置くなら超深めの {fc_limit:,.0f} 円に1枚。")

        # ==================== 🌙 夜間ハントモードのロジック ====================
        else:
            st.markdown("### 🦉 ナイトセッション特化・罠設置シミュレーション")
            
            if cme_diff <= -500 or prev_vix >= 24:
                st.error("📉 【夜間急落アラート】海外勢の売り浴びせが発生中、または地合い悪化です！")
                night_target = latest_cme - 250
                st.warning(f"**👉 ニューヨーク時間特有の『行き過ぎた下げヒゲ』を狙って罠を仕掛けます。**")
                st.info(f"**💡 夜間買い指値価格: {night_target:,.0f} 円**（マイクロ1枚・翌朝まで有効）")
                st.caption("※注文を入れたらPCを閉じ、枕を高くして寝てください。朝起きて約定していれば、日中の反発リバウンドを狙います。")
            else:
                st.success("✨ 【夜間平穏】海外市場は極めて平穏です。")
                st.write("夜間に無理に動く必要はありません。今夜は仕掛けを見送り、ぐっすり眠りましょう。")

        st.markdown("---")
        st.info("⚠️ **【20万運用ルール】** 昼に1枚買えている場合は、夜間の罠は仕掛けないでください（同時保有は常に1枚まで）。")
else:
    st.info("上のボタンを押すと、選択した時間帯に応じた最適な作戦を表示します。")
