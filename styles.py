import streamlit as st


def lade_css():

    st.markdown(
        """
        <style>

        .stApp {
            background-color: #f5f5f5;
        }

        .kunst-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-top: 0.5rem;
            margin-bottom: 0.3rem;
            line-height: 1.2;
            min-height: 2.5rem;
        }

        .kunst-meta {
            font-size: 0.88rem;
            color: #444;
            line-height: 1.45;
            min-height: 5rem;
        }

        .fixed-image-box {
            width: 100%;
            aspect-ratio: 1 / 1;
            overflow: hidden;
            border-radius: 10px;
            background: #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .fixed-image-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        @media (max-width: 768px) {

            .kunst-title {
                font-size: 0.95rem;
            }

            .kunst-meta {
                font-size: 0.8rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )