import streamlit as st


def lade_css():

    st.markdown(
        """
        <style>

        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }

        .block-container {
            max-width: 1160px;
            padding-top: 2.4rem;
            padding-left: 1.8rem;
            padding-right: 1.8rem;
        }

        section[data-testid="stSidebar"] {
            background-color: #262730;
        }

        h1 {
            font-size: 2.25rem;
            letter-spacing: -0.03em;
            margin-bottom: 0.3rem;
        }

        h2, h3, h4, h5, h6,
        p, label, span, div {
            color: #f5f5f5;
        }

        .fixed-image-box {
            width: 100%;
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #141820;
            border-radius: 13px;
            overflow: hidden;
            margin-bottom: 0.65rem;
        }

        .fixed-image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .kunst-title {
            height: 2.5em;
            overflow: hidden;
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.45rem;
            margin-bottom: 0.35rem;
            color: #ffffff;
        }

        .kunst-meta-kompakt {
            min-height: 2.3em;
            font-size: 0.82rem;
            line-height: 1.35;
            color: #d1d5db;
            margin-bottom: 0.45rem;
        }

        .kunst-meta {
            min-height: 4.3em;
            font-size: 0.84rem;
            line-height: 1.4;
            color: #e6e6e6;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding-top: 0.32rem;
            padding-bottom: 0.32rem;
            min-height: 2.25rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 14px;
            padding: 0.65rem;
        }

        div[data-testid="column"] {
            padding-left: 0.38rem;
            padding-right: 0.38rem;
        }

        input, textarea, select {
            border-radius: 8px !important;
        }

        /* Tablet */
        @media (max-width: 900px) {

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.8rem;
            }

            h1 {
                font-size: 1.9rem;
            }

            .fixed-image-box {
                height: 230px;
            }

            .kunst-title {
                font-size: 0.96rem;
                height: auto;
            }

            .kunst-meta-kompakt {
                font-size: 0.82rem;
                min-height: auto;
            }

        }

        /* Smartphone */
        @media (max-width: 640px) {

            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
                padding-top: 1rem;
            }

            h1 {
                font-size: 1.55rem;
                line-height: 1.15;
            }

            .fixed-image-box {
                height: 280px;
                border-radius: 12px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                padding: 0.65rem;
                margin-bottom: 1rem;
                border-radius: 13px;
            }

            .kunst-title {
                font-size: 1rem;
                height: auto;
                margin-top: 0.6rem;
            }

            .kunst-meta-kompakt {
                font-size: 0.86rem;
                margin-bottom: 0.6rem;
            }

            .stButton > button,
            .stDownloadButton > button {
                min-height: 2.6rem;
                font-size: 1rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )