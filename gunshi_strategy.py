import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ページ基本設定
st.set_page_config(page_title="取引所CFDコバンザメ投資計画", layout="wide")

st.title("🦅 取引所CFDコバンザメ投資計画")
st.caption("〜20万円資金・1日2回（朝8:30 / 夕方16:30）チェック用・ATR＆出来高解析対応〜")

# 資金・取引条件の設定 (日経225マイクロ：1ポイント=10円)
CAPITAL = 200000
MICRO_MULTIPLIER = 10 

# サイドバー設定
st.sidebar.header("⏰ 確認セッション選択")
session = st.sidebar.radio(
    "実行タイミングを選択してください",
    ["🌅 朝ハント（8:30前後）: 日中セッション（8:45〜15:45）向け", 
     "🌙 夕方ハント（16:30前後）: ナイトセッション（16:30〜翌6:00）向け"]
)

st.sidebar.markdown("---")
st.sidebar.write("**【提案B・動的適応モード適用中】**")
st.sidebar.write("・基本許容リスク：資金の約3.5%（±7,000円基準）")
st.sidebar.write("・ATR（ボラティリティ）により幅を自動最適化")
st.sidebar.write("・出来高急増（機関投資家の参入）を自動検知")

# メイン処理
if st.button("🚀 最新データを解析して作戦を立案"):
    with st.spinner("市場データを高度解析中（ATR・出来高スパイク計算中）..."):
        try:
            # 日経225のデータを取得
            ticker = yf.Ticker("^N225")
            df = ticker.history(period="60d", interval="1d")

            if df.empty:
                st.error("データの取得に失敗しました。時間を置いて再試行してください。")
            else:
                # 1. 移動平均線 (トレンド判定)
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df['SMA50'] = df['Close'].rolling(window=50).mean()

                # 2. RSI (過熱感判定)
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))

                # 3. MACD (モメンタム判定)
                exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                df['MACD'] = exp1 - exp2
                df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

                # 4. ATR (ボラティリティ算出: 14日)
                high_low = df['High'] - df['Low']
                high_cp = (df['High'] - df['Close'].shift(1)).abs()
                low_cp = (df['Low'] - df['Close'].shift(1)).abs()
                df['TR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
                df['ATR'] = df['TR'].rolling(window=14).mean()

                # 5. 出来高スパイク (過去20日平均との比較)
                df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()

                latest = df.iloc[-1]
                current_price = latest['Close']
                rsi = latest['RSI']
                macd = latest['MACD']
                macd_sig = latest['Signal']
                sma20 = latest['SMA20']
                sma50 = latest['SMA50']
                atr = latest['ATR']
                vol_current = latest['Volume']
                vol_avg = latest['Vol_SMA20']

                # スコア判定 (全4項目)
                cond_trend = current_price > sma20 and sma20 > sma50
                cond_macd = macd > macd_sig
                cond_rsi = 40 < rsi < 65
                cond_vol = (vol_current > vol_avg * 1.2) if not pd.isna(vol_avg) and vol_avg > 0 else False

                score = sum([cond_trend, cond_macd, cond_rsi, cond_vol])

                # 信頼度表示とアクション
                if score == 4:
                    stars = "⭐️⭐️⭐️⭐️ (超高信頼度・鉄板パターン)"
                    action = "積極買付け推奨（大口参入＋パーフェクトトレンド）"
                    bg_color = "success"
                elif score == 3:
                    stars = "⭐️⭐️⭐️☆ (高信頼度)"
                    action = "買いエントリー推奨 (コバンザメ良好局面)"
                    bg_color = "success"
                elif score == 2:
                    stars = "⭐️⭐️☆☆ (中信頼度)"
                    action = "打診買い検討 (慎重に1枚のみ)"
                    bg_color = "warning"
                else:
                    stars = "⭐️☆☆☆ (低信頼度)"
                    action = "静観・様子見推奨 (市場に明確な方向感なし)"
                    bg_color = "error"

                st.markdown("---")
                st.subheader(f"📊 最新シグナル: {stars}")
                
                # 結果ボックス表示
                msg = f"**判定結果**: {action} | **日経平均現在価格**: {current_price:,.0f}円"
                if bg_color == "success":
                    st.success(msg)
                elif bg_color == "warning":
                    st.warning(msg)
                else:
                    st.error(msg)

                # チェック項目の可視化
                st.markdown("**【内部チェックリストの詳細】**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("トレンド (移動平均)", "上昇" if cond_trend else "中立/下落", "順順" if cond_trend else "注意")
                c2.metric("モメンタム (MACD)", "買いサイン" if cond_macd else "売り/様子見", "ゴールデンクロス" if cond_macd else "-")
                c3.metric("過熱感 (RSI)", f"{rsi:.1f}", "適正範囲" if cond_rsi else "過熱/冷え込み")
                c4.metric("大口資金 (出来高)", "急増中 (仕掛け)" if cond_vol else "通常レベル", "ファンド参入気配" if cond_vol else "通常")

                # ATRに基づく動的な損切り・利確幅の算出
                # 最短400円〜ATRに合わせたゆとり幅を設定
                raw_sl = int(atr * 1.0) if not pd.isna(atr) else 700
                sl_points = max(500, min(raw_sl, 900)) # 500円〜900円の範囲に収める安全装置
                
                tp1_points = int(sl_points * 1.5)  # リスクリワード 1.5倍
                tp2_points = int(sl_points * 2.5)  # リスクリワード 2.5倍

                sl_price = current_price - sl_points
                tp1_price = current_price + tp1_points
                tp2_price = current_price + tp2_points

                sl_amount = sl_points * MICRO_MULTIPLIER
                tp1_amount = tp1_points * MICRO_MULTIPLIER
                tp2_amount = tp2_points * MICRO_MULTIPLIER

                sl_pct = (sl_amount / CAPITAL) * 100
                tp1_pct = (tp1_amount / CAPITAL) * 100
                tp2_pct = (tp2_amount / CAPITAL) * 100

                # テーブルデータの構築
                plan_data = {
                    "区分": ["堅実利確 (TP1)", "勝負利確 (TP2)", "撤退・損切り (SL)"],
                    "目標価格": [f"{tp1_price:,.0f}円", f"{tp2_price:,.0f}円", f"{sl_price:,.0f}円"],
                    "変動幅": [f"+{tp1_points:,}円", f"+{tp2_points:,}円", f"-{sl_points:,}円"],
                    "資金比率 (%)": [f"+{tp1_pct:.2f}%", f"+{tp2_pct:.2f}%", f"-{sl_pct:.2f}%"],
                    "想定損益額 (1枚)": [f"+{tp1_amount:,.0f}円", f"+{tp2_amount:,.0f}円", f"-{sl_amount:,.0f}円"],
                    "戦略の根拠": [
                        f"本日のATR({int(atr) if not pd.isna(atr) else 700}円)準拠 1.5倍目標",
                        "トレンド継続時の最大目標 (2.5倍)",
                        "市場の荒れ具合に合わせた動的ノイズガード"
                    ]
                }

                st.markdown("---")
                st.subheader(f"🎯 本日セッションの動的目標（ATR算出値: {int(atr) if not pd.isna(atr) else '標準'}円幅）")
                st.table(pd.DataFrame(plan_data))

                st.markdown("---")
                st.subheader("⚔️ 朝・夕の規律（IFD注文のガイド）")
                st.info(
                    f"**選択中: {session}**\n\n"
                    "1. アプリのシグナルが **⭐️3つ以上** であれば、提示された「目標価格」と「損切り価格」を使ってSBI証券で **IFD注文（エントリー＋決済予約）** を発注します。\n"
                    "2. 注文を入れたら、**次の確認時間（朝なら夕方16:30、夕方なら翌朝8:30）までアプリも証券画面も閉じます。**\n"
                    "3. 途中の上下動はすべて「機関投資家の揺さぶり」としてシステムに任せて放置するのが勝率を安定させるコツです。"
                )

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
else:
    st.write("上のボタンを押すと、最新のATRと出来高に基づいた作戦を立案します。")
