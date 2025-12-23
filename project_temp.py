import pandas as pd
import streamlit as st
import re
import time
import random
import string
from datetime import datetime
import altair as alt
import base64


DB_PATH = "DB.xlsx" 
INTRO_GIF = "intro_raw.gif"
# BACK_IMG = "background.png"


BAND_1 = range(0, 7)      # 0~6
BAND_2 = range(7, 10)     # 7~9
BAND_3 = range(10, 16)    # 10~15


def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def sid():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{ts}_{r}"






def set_background(img_path: str):

    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <style>
        /* 앱 전체 배경 */
        div[data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{b64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* 글 가독성: 레이아웃(패딩)은 건드리지 않고 배경만 반투명 처리 */
        div.block-container {{
            background: rgba(255, 255, 255, 0.86);
            border-radius: 16px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_css():
    st.markdown(
        """
        <style>
        div[data-testid="stVideo"] video {
            max-height: 36vh !important;
            width: 100% !important;
            height: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # set_background(BACK_IMG)




@st.cache_data
def load_questions(path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="questions")
    need = {"question_id", "question_text", "option_a", "option_b", "score1", "score2"}
    miss = need - set(df.columns)

    df = df.sort_values("question_id").reset_index(drop=True)
    df["score1"] = pd.to_numeric(df["score1"], errors="coerce").fillna(0).astype(int)
    df["score2"] = pd.to_numeric(df["score2"], errors="coerce").fillna(0).astype(int)
    return df


def load_responses(path) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name="responses")
    except Exception:
        return pd.DataFrame()


def save_responses(path, responses_df: pd.DataFrame, questions_df: pd.DataFrame):
    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        questions_df.to_excel(writer, index=False, sheet_name="questions")
        responses_df.to_excel(writer, index=False, sheet_name="responses")


def bold_quotes(text):
    if text is None:
        return ""
    s = str(text)
    s = re.sub(r'"([^"]+)"', r'"<strong>\1</strong>"', s)
    s = re.sub(r'“([^”]+)”', r'“<strong>\1</strong>”', s)
    return s.replace("\n", "<br>")


def type_by_score(score: int):
    if score in BAND_1:
        return "🔴감정 재접속형"
    elif score in BAND_2:
        return "🟠감정 잔존형"
    else:
        return "🟢이별 종료형"


def ex_status_sentence(result_type: str, ex_name: str) -> str:
    """
    결과 유형에 따라 전 애인 상태 설명 문장 생성.
    (초급 수준: if/elif/else)
    """
    ex = ex_name.strip() or "전 애인"

    if "🔴" in result_type:
        return f"아직 **{ex}**을(를) 완전히 잊지 못한 상태에 가깝습니다."
    elif "🟠" in result_type:
        return f"**{ex}**에 대한 감정은 남아 있지만, 일상으로 돌아가는 중입니다."
    else:
        return f"**{ex}**을(를) 대부분 정리했고, 이별을 ‘끝’으로 받아들인 상태에 가깝습니다."


def init():
    st.session_state.setdefault("page", "intro")
    st.session_state.setdefault("name", "")
    st.session_state.setdefault("gender", None)
    st.session_state.setdefault("ex", "")
    st.session_state.setdefault("session_id", "")
    st.session_state.setdefault("q_idx", 0)
    st.session_state.setdefault("score", 0)
    st.session_state.setdefault("answers", [])
    st.session_state.setdefault("saved", False)


def reset(to_page="intro"):
    st.session_state["q_idx"] = 0
    st.session_state["score"] = 0
    st.session_state["answers"] = []
    st.session_state["saved"] = False
    st.session_state["session_id"] = ""
    st.session_state["page"] = to_page


def intro_page():
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")


    c1, c2, c3 = st.columns([1.3, 3, 1])
    with c2:
        st.title("이별 극복 테스트💔")
    c1, c2, c3 = st.columns([1.2, 5, 1])
    with c2:
        st.subheader("전 애인의 DM, 당신은 얼마나 흔들릴까?")

    if st.button("시작하기", width="stretch"):
        st.session_state["page"] = "guide"
        rerun()
    st.image(
        INTRO_GIF,
        width="stretch"
    )


def info_page():
    st.header("기본 정보 입력")
    st.session_state["name"] = st.text_input("이름 또는 닉네임 (필수)", value=st.session_state["name"])
    st.session_state["gender"] = st.radio("성별 (필수)", ["남", "여"], index=None, key="gender_radio")
    st.caption("성별 정보는 테스트 결과에 영향을 주지 않습니다.")
    st.session_state["ex"] = st.text_input("전 애인 닉네임 (필수)", value=st.session_state["ex"])

    ok = (
        st.session_state["name"].strip()
        and st.session_state["ex"].strip()
        and st.session_state["gender"] in ["남", "여"]
    )
    if not ok:
        st.warning("이름/성별/전 애인 닉네임을 모두 입력해야 다음으로 진행할 수 있습니다.")

    if st.button("시작하기", disabled=not ok):
        reset("q")
        st.session_state["session_id"] = sid()
        rerun()


def guide_page():
    st.header("시작 전 안내")
    st.markdown("**지금부터 전 애인의 메시지가 다시 도착합니다.**")
    st.markdown("**당신의 선택이 이번 테스트의 결과를 만듭니다.**")
    st.markdown("---")
    st.markdown("이 테스트는 **총 15문항**으로 진행됩니다.")
    st.markdown("각 문항에서 **더 가까운 반응**을 하나 선택해 주세요.")
    st.markdown("정답은 없고, **솔직하게 선택할수록 결과가 정확**해집니다.")
    st.markdown("이 테스트에서 **성별 정보는 결과에 영향을 주지 않습니다**.")
    st.markdown("테스트가 끝나면 **결과 유형과 점수 구간 설명**을 확인할 수 있습니다.")
    st.markdown("---")

    if st.button("다음"):
        st.session_state["page"] = "info"
        rerun()


def question_page(qdf: pd.DataFrame):
    total = len(qdf)
    i = st.session_state["q_idx"]

    if i >= total:
        st.session_state["page"] = "loading"
        rerun()

    row = qdf.iloc[i]
    st.write(f"진행: {i+1} / {total}")
    st.progress((i + 1) / total)

    st.markdown("---")
    st.markdown(bold_quotes(row["question_text"]), unsafe_allow_html=True)
    st.markdown("---")

    a, b = str(row["option_a"]), str(row["option_b"])
    choice = st.radio("**선택지를 골라주세요**", [a, b], index=None, key=f"c_{i}")

    if st.button("다음"):
        if choice is None:
            st.warning("선택 후 다음으로 이동할 수 있어요")
            st.stop()

        sc = int(row["score1"]) if choice == a else int(row["score2"])
        st.session_state["score"] += sc
        st.session_state["answers"].append({"qid": int(row["question_id"]), "choice": choice, "score": sc})
        st.session_state["q_idx"] += 1

        if st.session_state["q_idx"] >= total:
            st.session_state["page"] = "loading"
        rerun()


def loading_page():
    st.header("결과 분석")
    with st.spinner("감정 반응 분석 중…"):
        time.sleep(3.0)
    st.session_state["page"] = "result"
    rerun()


def result_page(qdf: pd.DataFrame):
    if not st.session_state.get("saved"):
        try:
            resp = load_responses(DB_PATH)

            need_cols = ["session_id","timestamp","user_name","gender","ex_name","total_score","result_type"]
            for k in range(1, len(qdf) + 1):
                need_cols += [f"answer_{k}", f"answer_score_{k}"]

            if resp.empty:
                resp = pd.DataFrame(columns=need_cols)
            else:
                for c in need_cols:
                    if c not in resp.columns:
                        resp[c] = None

            score = int(st.session_state["score"])
            row = {
                "session_id": st.session_state["session_id"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_name": st.session_state["name"],
                "gender": st.session_state["gender"],
                "ex_name": st.session_state["ex"],
                "total_score": score,
                "result_type": type_by_score(score),
            }
            for idx, a in enumerate(st.session_state["answers"], start=1):
                row[f"answer_{idx}"] = a["choice"]
                row[f"answer_score_{idx}"] = a["score"]

            resp = pd.concat([resp, pd.DataFrame([row])], ignore_index=True)
            save_responses(DB_PATH, resp, qdf)
            st.session_state["saved"] = True
        except Exception as e:
            st.warning("응답 저장 중 오류가 발생했습니다. (통계에 반영되지 않을 수 있음)")
            st.exception(e)

    score = int(st.session_state["score"])
    rtype = type_by_score(score)

    st.header("결과")
    st.write(f"당신의 점수: **{score} / 15**")
    st.subheader(f"결과 유형: **{rtype}**")
    name = (st.session_state.get("name") or "").strip() or "당신"
    ex_name = (st.session_state.get("ex") or "").strip() or "전 애인"
    st.markdown(f"**{name}님은 {rtype}입니다.**")
    st.write(ex_status_sentence(rtype, ex_name))
    

    st.markdown("---")
    st.markdown(
        """
**❌ 이별 미극복 구간 (0–6점)**
- 감정 개입 빈번
- 반응 속도 빠름
- 관계 재진입 가능성 높음

**⚠ 경계 구간 (7–9점)**
- 행동은 차단하지만 감정은 잔존
- “이별은 했지만 끝난 느낌은 아님”

**✅ 이별 극복 구간 (10–15점)**
- 감정과 행동 일치
- DM이 와도 일상 유지
- 이별을 결정으로 처리한 상태
"""
    )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("끝내기"):
            st.session_state["page"] = "end"
            rerun()
    with col2:
        if st.button("내 주변 사람들은 어떤 유형이 많을까?"):
            st.session_state["page"] = "stats"
            rerun()


def stats_page():
    st.header("유형별 결과 현황")

    df = load_responses(DB_PATH)
    if df.empty or "result_type" not in df.columns:
        st.info("아직 저장된 결과가 없습니다.")
        return

    df = df.dropna(subset=["result_type"])
    if df.empty:
        st.info("아직 저장된 결과가 없습니다.")
        return

    counts = df["result_type"].astype(str).value_counts()
    order = ["🔴감정 재접속형", "🟠감정 잔존형", "🟢이별 종료형"]
    total = int(counts.sum())

    st.caption(f"**누적 표본 수: {total}명**")

    st.markdown("---")
    plot_df = pd.DataFrame({
    "유형": order,
    "명": [int(counts.get(t, 0)) for t in order],
})

    max_n = int(plot_df["명"].max()) if not plot_df.empty else 0
    if max_n < 1:
        max_n = 1  # 전부 0명일 때도 축이 보이도록

    chart = (
        alt.Chart(plot_df)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("유형:N", sort=order, axis=alt.Axis(title="유형", labelAngle=0)),
            y=alt.Y(
                "명:Q",
                scale=alt.Scale(domain=[0, max_n]),
                axis=alt.Axis(
                    title="명",
                    values=list(range(0, max_n + 1, 1)),  # ✅ 0,1,2,3...만
                    format="d",  # ✅ 정수 포맷
                ),
            ),
            color=alt.Color("유형:N", legend=None, scale=alt.Scale(scheme="category10")),
            tooltip=[alt.Tooltip("유형:N"), alt.Tooltip("명:Q")],
        )
        .properties(height=320)
    )

    st.altair_chart(chart, width="stretch")


    st.markdown("---")

    top = max(order, key=lambda k: int(counts.get(k, 0)))
    st.write(f"가장 많은 유형은 **{top}** 입니다.")

    st.markdown("---")
    col1, spacer, col3 = st.columns([3, 8, 2])
    with col1:
        if st.button("결과로 돌아가기"):
            st.session_state["page"] = "result"
            rerun()
    with col3:
        if st.button("끝내기"):
            st.session_state["page"] = "end"
            rerun()


def end_page():
    st.header("종료")
    st.write("테스트가 종료되었습니다. 브라우저 탭을 닫으면 완전히 종료됩니다.")
    st.stop()


def main():
    st.set_page_config(page_title="이별 극복 테스트", page_icon="💔", layout="centered")
    init()
    # apply_css()

    

    qdf = load_questions(DB_PATH)

    p = st.session_state["page"]
    if p == "intro":
        intro_page()
    elif p == "info":
        info_page()
    elif p == "guide":
        guide_page()
    elif p == "q":
        question_page(qdf)
    elif p == "loading":
        loading_page()
    elif p == "result":
        result_page(qdf)
    elif p == "stats":
        stats_page()
    elif p == "end":
        end_page()
    else:
        reset("intro")
        rerun()


if __name__ == "__main__":
    main()
