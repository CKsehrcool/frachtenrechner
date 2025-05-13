
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Frachtenrechner – Import & Export")
st.title("Frachtenrechner – Import & Export")
st.caption("Berechnung basierend auf Tarifzonen, Gewichtsklassen und Zuschlägen")

uploaded_file = st.file_uploader("Bitte Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    try:
        country_codes = pd.read_excel(uploaded_file, sheet_name="COUNTRY_CODES")
        zones = pd.read_excel(uploaded_file, sheet_name="Zonen")
        adds = pd.read_excel(uploaded_file, sheet_name="adds")
        rates = pd.read_excel(uploaded_file, sheet_name="Frachtraten")
        gk_table = pd.read_excel(uploaded_file, sheet_name="Gewichtsklassen")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Import")
            import_country = st.selectbox("Importland", country_codes["COUNTRY"], key="import_country")
            import_tarif = st.selectbox("Tarif (Import)", zones.columns[1:], key="import_tarif")
            import_weight = st.number_input("Importgewicht total (kg)", min_value=0.01, step=0.5, key="import_weight")

        with col2:
            st.subheader("Export")
            export_country = st.selectbox("Exportland", country_codes["COUNTRY"], key="export_country")
            export_tarif = st.selectbox("Tarif (Export)", zones.columns[1:], key="export_tarif")
            export_weight = st.number_input("Exportgewicht (Job) (kg)", min_value=0.01, step=0.5, key="export_weight")

        def berechne_kosten(country, tarif, weight, suffix):
            try:
                iso_row = country_codes[country_codes["COUNTRY"] == country]
                if iso_row.empty:
                    return f"{suffix}: Kein ISO-Code für Land gefunden.", None
                iso_code = iso_row["LAND"].values[0]

                zone_row = zones[zones["LAND"] == iso_code]
                if zone_row.empty:
                    return f"{suffix}: Keine Zone für Land gefunden.", None
                zone = zone_row[tarif].values[0]

                gk_row = gk_table[
                    (gk_table["TARIF"] == tarif) &
                    (gk_table["von"] <= weight) &
                    (gk_table["bis"] >= weight)
                ]
                if gk_row.empty:
                    return f"{suffix}: Keine Gewichtsklasse gefunden.", None
                gk = gk_row["GK"].values[0]

                rate_row = rates[(rates["TARIF"] == tarif) & (rates["GK"] == gk)]
                if zone not in rate_row.columns:
                    return f"{suffix}: Zone {zone} nicht im Tarifblatt gefunden.", None
                base_rate = rate_row[zone].values[0]

                zuschlag_row = adds[adds["TARIF"] == tarif]
                zuschlag = zuschlag_row["FUELSURCHARGE"].values[0] if not zuschlag_row.empty else 0

                surcharge = round(base_rate * zuschlag, 2)
                if weight > 20:
                    base_rate = base_rate * weight
                surcharge = round(base_rate * zuschlag, 2)
                total = round(base_rate + surcharge, 2)

                return None, {
                    "Basisrate": base_rate,
                    "Zuschlag": surcharge,
                    "Gesamtkosten": total
                }

            except Exception as err:
                return f"{suffix}: Fehler beim Verarbeiten – {err}", None

        err1, imp = berechne_kosten(import_country, import_tarif, import_weight, "Import")
        err2, exp = berechne_kosten(export_country, export_tarif, export_weight, "Export")

        st.subheader("Ergebnis")

        if err1:
            st.error(err1)
        elif imp:
            st.markdown("**Importkosten**")
            st.write(f"Frachtrate: {imp['Basisrate']} EUR")
            st.write(f"Zuschlag: {imp['Zuschlag']} EUR")
            st.success(f"Gesamt Import: {imp['Gesamtkosten']} EUR")

        if err2:
            st.error(err2)
        elif exp:
            st.markdown("**Exportkosten**")
            st.write(f"Frachtrate: {exp['Basisrate']} EUR")
            st.write(f"Zuschlag: {exp['Zuschlag']} EUR")
            st.success(f"Gesamt Export: {exp['Gesamtkosten']} EUR")

        if imp and exp:
            gesamt = round(imp["Gesamtkosten"] + exp["Gesamtkosten"], 2)
            st.markdown("---")
            st.success(f"**Gesamtkosten (Import + Export): {gesamt} EUR**")

            # Berechne Jobkosten
            anteil_import = round((export_weight / import_weight) * imp["Gesamtkosten"], 2)
            jobkosten = round(anteil_import + exp["Gesamtkosten"], 2)

            st.markdown("### 💼 Jobkosten")
            st.write(f"Anteilige Importkosten: {anteil_import} EUR")
            st.write(f"Vollständige Exportkosten: {exp['Gesamtkosten']} EUR")
            st.success(f"**Jobkosten: {jobkosten} EUR**")

    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Datei: {e}")