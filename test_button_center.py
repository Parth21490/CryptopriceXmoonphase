#!/usr/bin/env python3
"""
Test script to verify button centering works correctly.
"""

import streamlit as st

st.set_page_config(
    page_title="Button Center Test",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Button Centering Test")

st.markdown("### Before (not centered):")
if st.button("Not Centered Button", key="not_centered"):
    st.write("Button clicked!")

st.markdown("### After (centered):")
# Center the button using columns
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("Centered Button", key="centered", use_container_width=True):
        st.write("Centered button clicked!")

st.markdown("### Test Complete")
st.write("The second button should be centered in the middle column.")