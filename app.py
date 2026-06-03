import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(page_title="Kayfa | Employee Retention", layout="wide")


st.markdown("""
<style>
    .stApp {
        background: linear-gradient(140deg, #0F172A 0%, #1E1B4B 50%, #0F172A 100%);
    }
</style>
""", unsafe_allow_html=True)


def load_data():
    df = pd.read_csv('cleaned_employee_attrition.csv')
    
    ordinal_categories = {
        'work_life_balance': ['Poor', 'Fair', 'Good', 'Excellent'],
        'job_satisfaction': ['Low', 'Medium', 'High', 'Very High'],
        'job_level': ['Entry', 'Mid', 'Senior']
    }
    for col, order in ordinal_categories.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)
            
    df['age_group'] = pd.cut(df['age'], bins=[17, 25, 35, 45, 55, 100], labels=['18-25', '26-35', '36-45', '46-55', '56+'])
    df['commute_distance'] = pd.qcut(df['distance_from_home'], 3, labels=['Short Commute', 'Medium Commute', 'Long Commute'])
    df['years_per_promotion'] = df['years_at_company'] / (df['number_of_promotions'] + 1)
    df['loyalty_bucket'] = pd.qcut(df['years_per_promotion'], 3, labels=['Fast Track', 'Average Speed', 'Stagnant'])
    df['income_tier'] = pd.qcut(df['monthly_income'], 3, labels=['Lower Tier', 'Middle Tier', 'Upper Tier'])
    df['has_dependents_label'] = np.where(df['number_of_dependents'] > 0, 'Has Dependents', 'No Dependents')
    df['work_setting'] = df['remote_work'].map({0: 'In-Office', 1: 'Remote'})
    df['overtime_status'] = df['overtime'].map({0: 'Standard Hours', 1: 'Works Overtime'})
    
    return df

df = load_data()


col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("Kayfa.svg", use_container_width=True)
    except FileNotFoundError:
        st.markdown("<h2 style='color: #3B82F6; margin:0;'>Kayfa - كيف</h2>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='margin: 0;'>Employee Retention Dashboard</h1>", unsafe_allow_html=True)
    st.caption("A data-driven view into organizational health, turnover drivers, and operational bottlenecks.")

st.write("") 

with st.container(border=True):
    st.markdown("**Filter the Dashboard**")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        selected_roles = st.multiselect("Select Departments:", options=df['job_role'].unique(), default=df['job_role'].unique())
    with f_col2:
        selected_levels = st.multiselect("Select Seniority Levels:", options=df['job_level'].unique(), default=list(df['job_level'].unique()))

filtered_df = df[(df['job_role'].isin(selected_roles)) & (df['job_level'].isin(selected_levels))]
st.write("")


total_emp = len(filtered_df)
left_df = filtered_df[filtered_df['attrition'] == 1]
stayed_df = filtered_df[filtered_df['attrition'] == 0]
attrition_rate = (len(left_df) / total_emp) * 100 if total_emp > 0 else 0

st.markdown("### Quick Stats")

m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1.container(border=True):
    st.metric("Total Employees", f"{total_emp:,}")
with m2.container(border=True):
    st.metric("Turnover Rate", f"{attrition_rate:.1f}%")
with m3.container(border=True):
    st.metric("Avg Pay (All Staff)", f"${filtered_df['monthly_income'].mean():,.0f}")
with m4.container(border=True):
    st.metric("Avg Age (All Staff)", f"{filtered_df['age'].mean():.1f}")
with m5.container(border=True):
    st.metric("Avg Years at Company", f"{filtered_df['years_at_company'].mean():.1f} yrs")
with m6.container(border=True):
    st.metric("Total Promotions Given", f"{filtered_df['number_of_promotions'].sum():,}")

st.write("")



tab1, tab2, tab3, tab4 = st.tabs([
    "Demographics & Departments", 
    "Work Environment Analysis", 
    "Career & Satisfaction", 
    "High-Risk Profiles"
])

plotly_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#F8FAFC"),
    margin=dict(t=50, b=30, l=40, r=20)
)



with tab1:
    st.markdown("**Overview:** Identify which specific demographics and departments are experiencing the highest exit rates.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        # FIX: Removed the confusing promotion multiplier. Just raw, honest numbers now.
        profile_stats = pd.DataFrame({
            'Attribute': ['Age', 'Commute Distance (miles)', 'Years at Company'],
            'Stayed': [stayed_df['age'].mean(), stayed_df['distance_from_home'].mean(), stayed_df['years_at_company'].mean()],
            'Left': [left_df['age'].mean(), left_df['distance_from_home'].mean(), left_df['years_at_company'].mean()]
        })
        fig_profile = go.Figure(data=[
            go.Bar(name='Stayed', x=profile_stats['Attribute'], y=profile_stats['Stayed'], marker_color='#2563EB'),
            go.Bar(name='Left', x=profile_stats['Attribute'], y=profile_stats['Left'], marker_color='#F43F5E')
        ])
        fig_profile.update_layout(**plotly_layout, barmode='group', title="<b>Average Traits: Employees Who Stayed vs. Left</b>")
        st.plotly_chart(fig_profile, use_container_width=True)
        
    with col_b:
        dept_att = filtered_df.groupby('job_role', observed=True)['attrition'].mean().reset_index().sort_values('attrition')
        dept_att['Turnover Rate (%)'] = dept_att['attrition'] * 100
        fig_dept = px.bar(dept_att, x='Turnover Rate (%)', y='job_role', orientation='h', color='Turnover Rate (%)', color_continuous_scale='Blues', labels={'job_role': 'Department'})
        fig_dept.update_layout(**plotly_layout, title="<b>Turnover by Department</b>", coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_dept, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        age_att = filtered_df.groupby('age_group', observed=True)['attrition'].mean().reset_index()
        age_att['Turnover Rate (%)'] = age_att['attrition'] * 100
        fig_age = px.bar(age_att, x='age_group', y='Turnover Rate (%)', color='Turnover Rate (%)', color_continuous_scale='PuBu', labels={'age_group': 'Age Bracket'})
        fig_age.update_layout(**plotly_layout, title="<b>Turnover by Age Group</b>", coloraxis_showscale=False)
        st.plotly_chart(fig_age, use_container_width=True)
        
    with col_d:
        edu_att = filtered_df.groupby('education_level', observed=True)['attrition'].mean().reset_index()
        edu_att['Turnover Rate (%)'] = edu_att['attrition'] * 100
        fig_edu = px.bar(edu_att, x='Turnover Rate (%)', y='education_level', orientation='h', color='Turnover Rate (%)', color_continuous_scale='OrRd', labels={'education_level': 'Education Level'})
        fig_edu.update_layout(**plotly_layout, title="<b>Turnover by Education Level</b>", coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_edu, use_container_width=True)



with tab2:
    st.markdown("**Work Environment:** Measuring how the physical and temporal work environment impacts retention.")
    
    c1, c2 = st.columns(2)
    with c1:
        wlb_fam = filtered_df.groupby(['has_dependents_label', 'work_life_balance'], observed=True)['attrition'].mean().reset_index()
        wlb_fam['Turnover Rate (%)'] = wlb_fam['attrition'] * 100
        fig_wlb = px.line(wlb_fam, x='work_life_balance', y='Turnover Rate (%)', color='has_dependents_label', markers=True, color_discrete_map={'Has Dependents': '#10B981', 'No Dependents': '#3B82F6'}, labels={'work_life_balance': 'Work-Life Balance Rating', 'has_dependents_label': 'Family Status'})
        fig_wlb.update_traces(line=dict(width=4), marker=dict(size=10))
        fig_wlb.update_layout(**plotly_layout, title="<b>The Work-Life Balance Impact</b><br><sup>Single employees quit even faster when personal time is compromised.</sup>", legend_title="")
        st.plotly_chart(fig_wlb, use_container_width=True)
        
    with c2:
        remote_commute = filtered_df.groupby(['work_setting', 'commute_distance'], observed=True)['attrition'].mean().reset_index()
        remote_commute['Turnover Rate (%)'] = remote_commute['attrition'] * 100
        fig_remote = px.bar(remote_commute, x='commute_distance', y='Turnover Rate (%)', color='work_setting', barmode='group', color_discrete_map={'In-Office': '#4F46E5', 'Remote': '#06B6D4'}, labels={'commute_distance': 'Commute Type', 'work_setting': 'Work Setting'})
        fig_remote.update_layout(**plotly_layout, title="<b>The Remote Work Shield</b><br><sup>Working remotely significantly drops turnover regardless of commute length.</sup>", legend_title="")
        st.plotly_chart(fig_remote, use_container_width=True)
    
    overtime_income = filtered_df.groupby(['income_tier', 'overtime_status'], observed=True)['attrition'].mean().unstack() * 100
    fig_heat = px.imshow(overtime_income, color_continuous_scale='PuBuGn', text_auto=".1f", aspect="auto", labels=dict(x="Overtime Schedule", y="Compensation Bracket", color="Turnover %"))
    fig_heat.update_layout(**plotly_layout, title="<b>Paycheck vs. Extra Hours</b><br><sup>High salaries do NOT stop employees from quitting if they are forced to work overtime.</sup>")
    st.plotly_chart(fig_heat, use_container_width=True)


with tab3:
    st.markdown("**Career Velocity:** How promotions, seniority, and internal satisfaction affect loyalty.")
    
    c3, c4 = st.columns(2)
    with c3:
        lvl_att = filtered_df.groupby('job_level', observed=True)['attrition'].mean().reset_index()
        lvl_att['Turnover Rate (%)'] = lvl_att['attrition'] * 100
        fig_lvl = px.bar(lvl_att, x='job_level', y='Turnover Rate (%)', color='Turnover Rate (%)', color_continuous_scale='Teal', labels={'job_level': 'Seniority Level'})
        fig_lvl.update_layout(**plotly_layout, title="<b>Turnover by Seniority Level</b><br><sup>Entry-level employees quit at a massive 63% rate.</sup>", coloraxis_showscale=False)
        st.plotly_chart(fig_lvl, use_container_width=True)
        
    with c4:
        promo_att = filtered_df.groupby('loyalty_bucket', observed=True)['attrition'].mean().reset_index()
        promo_att['Turnover Rate (%)'] = promo_att['attrition'] * 100
        fig_promo = px.bar(promo_att, x='loyalty_bucket', y='Turnover Rate (%)', color='Turnover Rate (%)', color_continuous_scale='emrld', labels={'loyalty_bucket': 'Promotion Speed'})
        fig_promo.update_layout(**plotly_layout, title="<b>The Promotion Trap (Poaching Risk)</b>", coloraxis_showscale=False)
        st.plotly_chart(fig_promo, use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        sat_att = filtered_df.groupby('job_satisfaction', observed=True)['attrition'].mean().reset_index()
        sat_att['Turnover Rate (%)'] = sat_att['attrition'] * 100
        fig_sat = px.bar(sat_att, x='job_satisfaction', y='Turnover Rate (%)', color='Turnover Rate (%)', color_continuous_scale='Purples', labels={'job_satisfaction': 'Self-Reported Job Satisfaction'})
        fig_sat.update_layout(**plotly_layout, title="<b>The Satisfaction Paradox</b><br><sup>Highly satisfied employees leave just as fast as miserable ones.</sup>", coloraxis_showscale=False)
        st.plotly_chart(fig_sat, use_container_width=True)

    with c6:
        sample_df = filtered_df.sample(n=min(1000, len(filtered_df)), random_state=42)
        sample_df['Status'] = sample_df['attrition'].map({0: 'Stayed', 1: 'Left'})
        fig_scatter = px.scatter(sample_df, x='years_at_company', y='monthly_income', color='Status', opacity=0.7, color_discrete_sequence=['#3B82F6', '#EF4444'], labels={'years_at_company': 'Years at Company', 'monthly_income': 'Monthly Pay'})
        fig_scatter.update_layout(**plotly_layout, title="<b>Income vs. Years at Company</b><br><sup>Visualizing where the exits happen over time.</sup>", legend_title="")
        st.plotly_chart(fig_scatter, use_container_width=True)


with tab4:
    st.markdown("### Most Vulnerable Employee Groups")
    st.markdown("These specific combinations of factors act as structural traps, pushing employees out the door at elevated rates.")
    st.write("")
    
    p1, p2 = st.columns(2)
    
    worst_case = filtered_df[(filtered_df['job_level'] == 'Entry') & (filtered_df['remote_work'] == 0) & (filtered_df['work_life_balance'] == 'Poor')]
    worst_case_rate = (worst_case['attrition'].mean() * 100) if len(worst_case) > 0 else 0
    
    with p1.container(border=True):
        st.markdown("<h4 style='color: #F43F5E; margin-top:0;'>The Burnout Trap</h4>", unsafe_allow_html=True)
        st.markdown("**Who they are:** Entry-Level + Required in Office + Poor Work-Life Balance")
        st.markdown("This combination of zero flexibility and demanding junior schedules drives attrition to staggering heights.")
        
        st.write("")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Turnover Risk Level", f"{worst_case_rate:.1f}%")
        col_m2.metric("Total Employees Affected", f"{len(worst_case):,}")
        
    high_value_risk = filtered_df[(filtered_df['performance_rating'] == 'High') & (filtered_df['income_tier'] == 'Lower Tier') & (filtered_df['loyalty_bucket'] == 'Stagnant')]
    high_value_rate = (high_value_risk['attrition'].mean() * 100) if len(high_value_risk) > 0 else 0
    
    with p2.container(border=True):
        st.markdown("<h4 style='color: #FBBF24; margin-top:0;'>The Under-Rewarded Stars</h4>", unsafe_allow_html=True)
        st.markdown("**Who they are:** High Performers + Lower Pay Bracket + No Recent Promotions")
        st.markdown("These are top-tier workers producing great results, but they are being ignored for promotions and paid less than their peers.")
        
        st.write("")
        col_m3, col_m4 = st.columns(2)
        col_m3.metric("Turnover Risk Level", f"{high_value_rate:.1f}%")
        col_m4.metric("Total Employees Affected", f"{len(high_value_risk):,}")
