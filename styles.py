import streamlit as st


def lade_css():
    st.markdown(
        """
        <style>
        .fixed-image-box {
            width: 100%;
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #141820;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.6rem;
        }

        .fixed-image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .kunst-title {
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.4rem;
            margin-bottom: 0.3rem;
        }

        .kunst-meta-kompakt {
            font-size: 0.8rem;
            line-height: 1.3;
            margin-bottom: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

