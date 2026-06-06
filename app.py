import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(page_title="Kayfa | Talent Leak Dashboard", layout="wide", initial_sidebar_state="expanded")


try:
    st.logo("Kayfa.svg")
except:
    pass

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('cleaned_employee_attrition.csv')
    except FileNotFoundError:
        df = pd.read_csv('employee_attrition_combined.csv')
        
    if set(df['attrition'].unique()).issubset({0, 1}) or df['attrition'].dtype in [np.int64, np.float64]:
        df['Attrition Status'] = df['attrition'].map({0: 'Stayed', 1: 'Left'})
        df['left_numeric'] = df['attrition']
    else:
        df['Attrition Status'] = df['attrition']
        df['left_numeric'] = (df['attrition'] == 'Left').astype(int)

    ordinal_categories = {
        'work_life_balance': ['Poor', 'Fair', 'Good', 'Excellent'],
        'job_satisfaction': ['Low', 'Medium', 'High', 'Very High'],
        'job_level': ['Entry', 'Mid', 'Senior']
    }
    for col, order in ordinal_categories.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)
            
    df['Remote Work Status'] = df['remote_work'].replace({0: 'In-Office', 1: 'Remote', 'No': 'In-Office', 'Yes': 'Remote'})
    df['Overtime Status'] = df['overtime'].replace({0: 'No Overtime', 1: 'Overtime', 'No': 'No Overtime', 'Yes': 'Overtime'})
    
    df['Tenure Stage'] = pd.cut(df['years_at_company'], bins=[-1, 1, 4, 9, 15, 100], 
                                labels=['0-1 yrs (New)', '2-4 yrs (Early)', '5-9 yrs (Mid)', '10-15 yrs (Senior)', '15+ yrs (Veteran)'])
    return df

df = load_data()
company_avg_attrition = df['left_numeric'].mean()
brand_color = '#3B82F6' 


def render_page_header(title, subtitle=None):
    col_text, col_logo = st.columns([5, 1])
    with col_text:
        st.title(title)
        if subtitle:
            st.caption(subtitle)
    with col_logo:
        try:
            st.image("Kayfa.svg", width=120)
        except:
            st.markdown("<h3 style='color: #3B82F6; text-align: right; margin-top: 15px;'>Kayfa</h3>", unsafe_allow_html=True)
    st.write("") 

def add_average_line(fig, avg_val, name="Company Average"):
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="red", dash="dash"), name=name))
    fig.add_hline(y=avg_val, line_dash="dash", line_color="red")
    return fig


def page_overview():
    render_page_header("Company Overview & Main Leaks", "A clear view of our turnover problem and where we are losing the most staff.")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Employees", f"{len(df):,}")
    m2.metric("Overall Turnover Rate", f"{company_avg_attrition * 100:.1f}%")
    m3.metric("Total Exits", f"{df['left_numeric'].sum():,}")
    m4.metric("Remote Staff", f"{(df['Remote Work Status'] == 'Remote').mean() * 100:.1f}%")
    
    st.divider()
    
    st.markdown("### Q1: Department Breakdown")
    role_stats = df.groupby('job_role')['left_numeric'].agg(['count', 'sum', 'mean']).reset_index()
    role_stats.columns = ['Department', 'Total', 'Exits', 'Turnover Rate']
    role_stats['Turnover %'] = role_stats['Turnover Rate'] * 100
    
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(role_stats.sort_values('Turnover %', ascending=False), x='Department', y='Turnover %', 
                      text_auto='.1f', color_discrete_sequence=[brand_color])
        fig1 = add_average_line(fig1, company_avg_attrition * 100)
        fig1.update_layout(title="<b>Turnover Rate by Department</b>", yaxis_title="Turnover Rate (%)")
        st.plotly_chart(fig1, use_container_width=True, theme="streamlit")
    with col2:
        fig2 = px.bar(role_stats.sort_values('Exits', ascending=False), x='Department', y='Exits', 
                      text_auto=True, color_discrete_sequence=['#94A3B8'])
        fig2.update_layout(title="<b>Total Exits (Headcount)</b>", yaxis_title="Number of People")
        st.plotly_chart(fig2, use_container_width=True, theme="streamlit")

    st.info("**Insight:** Education is completely broken (49% quit rate). Technology is draining our budget because replacing 9,000+ specialized workers is highly expensive.")
    st.error("**Action:** Replace the management in the Education department. For Tech, give immediate retention bonuses to top performers to stop the bleeding.")


def page_demographics():
    render_page_header("Who is Leaving?")
    
    st.markdown("### Q7: Life Stage Risk Profiles")
    df['Life Stage Profile'] = np.where((df['age'] < 30) & (df['marital_status'] == 'Single') & (df['number_of_dependents'] == 0), 
                                'Under 30, Single, No Kids', 'All Other Demographics')
    life_stats = df.groupby('Life Stage Profile')['left_numeric'].mean().reset_index()
    life_stats['Turnover %'] = life_stats['left_numeric'] * 100
    
    fig3 = px.bar(life_stats, x='Life Stage Profile', y='Turnover %', text_auto='.1f', 
                  color_discrete_sequence=[brand_color]) 
    fig3 = add_average_line(fig3, company_avg_attrition * 100)
    fig3.update_layout(title="<b>The Young & Single Flight Risk</b>", yaxis_title="Turnover Rate (%)")
    st.plotly_chart(fig3, use_container_width=True, theme="streamlit")

    st.info("**Insight:** Young, single employees without kids quit at a massive 73.3% rate. They have no family ties to our benefits plan, so they chase better offers fast.")
    st.error("**Action:** Stop selling them family benefits. Give this group fast-track promotions, constant training, and clear paths to leadership. Move them up or they will move out.")


def page_environment():
    render_page_header("Burnout & Flexibility")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Q2: The Cost of Overtime")
        ot_stats = df.groupby('Overtime Status')['left_numeric'].mean().reset_index()
        ot_stats['Turnover %'] = ot_stats['left_numeric'] * 100
        fig_ot = px.bar(ot_stats, x='Overtime Status', y='Turnover %', text_auto='.1f', color_discrete_sequence=[brand_color])
        fig_ot.update_layout(title="<b>Turnover: Standard vs. Overtime Hours</b>", yaxis_title="Turnover Rate (%)")
        st.plotly_chart(fig_ot, use_container_width=True, theme="streamlit")
        
        st.info("**Insight:** Overtime increases quitting by 6%. But even without it, normal hours still have a bad 45.5% turnover rate.")
        st.error("**Action:** Ban excessive overtime today. But do not stop there—fix base pay and team culture, because working regular hours is not keeping people here.")

    with col2:
        st.markdown("### Q3: Remote Work")
        rw_stats = df.groupby('Remote Work Status')['left_numeric'].mean().reset_index()
        rw_stats['Turnover %'] = rw_stats['left_numeric'] * 100
        fig_rw = px.bar(rw_stats, x='Remote Work Status', y='Turnover %', text_auto='.1f', color_discrete_sequence=[brand_color])
        fig_rw.update_layout(title="<b>Turnover: In-Office vs. Remote</b>", yaxis_title="Turnover Rate (%)")
        st.plotly_chart(fig_rw, use_container_width=True, theme="streamlit")
        
        st.info("**Insight:** Remote work cuts turnover in half (24% vs 52%). But right now, only 19% of our staff are allowed to do it.")
        st.error("**Action:** Make hybrid work a standard company policy for just a month. Give every eligible employee at least two work-from-home days a week starting next month.")

    st.divider()

    st.markdown("### Q6: Passion vs. Burnout")
    wlb_sat = df.groupby(['job_satisfaction', 'work_life_balance'], observed=True)['left_numeric'].mean().unstack() * 100
    fig_heat = px.imshow(wlb_sat, text_auto=".1f", color_continuous_scale='Blues', aspect="auto",
                         labels=dict(x="Work-Life Balance", y="Job Satisfaction", color="Turnover %"))
    fig_heat.update_layout(title="<b>Turnover by Satisfaction & Work-Life Balance</b>")
    st.plotly_chart(fig_heat, use_container_width=True, theme="streamlit")

    st.info("**Insight:** Employees who love their jobs but have terrible work-life balance quit at the exact same rate (65%) as people who hate their jobs.")
    st.error("**Action:** Force your top performers to log off. Do not let managers overwork people just because the employee is passionate.")



def page_career():
    render_page_header("Money & Career Growth")

    st.markdown("### Q5: The 5-Year Wall")
    tenure_stats = df.groupby('Tenure Stage', observed=True)['left_numeric'].mean().reset_index()
    tenure_stats['Turnover %'] = tenure_stats['left_numeric'] * 100
    fig_time = px.line(tenure_stats, x='Tenure Stage', y='Turnover %', markers=True)
    fig_time.update_traces(line=dict(color=brand_color, width=4), marker=dict(size=10))
    fig_time = add_average_line(fig_time, company_avg_attrition * 100)
    fig_time.update_layout(title="<b>Turnover by Years at Company</b>", yaxis_title="Turnover Rate (%)")
    st.plotly_chart(fig_time, use_container_width=True, theme="streamlit")

    st.info("**Insight:** Employee turnover is highest during the first 6–8 years. Many employees are still exploring opportunities, building their careers, and moving between roles or companies.")
    st.error("**Action:** Run short anonymous surveys to understand why employees leave and identify issues before they lead to turnover.")
    
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Q4: Pay Fairness")
        df['Pay Tier (Entry)'] = df[df['job_level'] == 'Entry'].groupby('job_level', observed=True)['monthly_income'].transform(
            lambda x: pd.qcut(x, q=4, labels=['Bottom 25%', 'Q2', 'Q3', 'Top 25%'], duplicates='drop'))
        pay_stats = df[df['job_level'] == 'Entry'].groupby('Pay Tier (Entry)', observed=True)['left_numeric'].mean().reset_index()
        pay_stats['Turnover %'] = pay_stats['left_numeric'] * 100
        
        fig_pay = px.bar(pay_stats, x='Pay Tier (Entry)', y='Turnover %', text_auto='.1f', color_discrete_sequence=[brand_color])
        fig_pay.update_layout(title="<b>Turnover by Pay Tier (Entry Level Only)</b>", yaxis_title="Turnover Rate (%)")
        st.plotly_chart(fig_pay, use_container_width=True, theme="streamlit")
        
        st.info("**Insight:** Maxing out an employee's pay bracket does not stop them from leaving. Entry-level staff quit at 62% even when paid top dollar.")
        st.error("**Action:** Stop giving tiny 2% raises to save people. Promote them to the next job level or fire their bad manager.")

    with col2:
        st.markdown("### Q8: Career Stagnation")
        df['Career Mobility'] = np.where(df['number_of_promotions'] == 0, '0 Promotions (Stuck)', '1+ Promotions (Moving Up)')
        stag_stats = df.groupby('Career Mobility')['left_numeric'].mean().reset_index()
        stag_stats['Turnover %'] = stag_stats['left_numeric'] * 100
        
        fig_stag = px.bar(stag_stats, x='Career Mobility', y='Turnover %', text_auto='.1f', color_discrete_sequence=[brand_color])
        fig_stag.update_layout(title="<b>Stuck vs. Moving Up</b>", yaxis_title="Turnover Rate (%)")
        st.plotly_chart(fig_stag, use_container_width=True, theme="streamlit")
        
        st.info("**Insight:** Stuck employees quit at 50%. But people getting promoted still quit at 45%. A new title is not a magic fix.")
        st.error("**Action:** Protect the workload of newly promoted staff. If you give them a new title but work them to death, they will leave anyway.")


def page_strategy():
    render_page_header("Final Strategy & Action Plan")
    
    st.markdown("### Q9: The Danger Zone")
    worst_case = df[(df['Remote Work Status'] == 'In-Office') & 
                    (df['work_life_balance'] == 'Poor') & 
                    (df['marital_status'] == 'Single') & 
                    (df['Overtime Status'] == 'Overtime')]
    
    worst_case_rate = worst_case['left_numeric'].mean() * 100 if len(worst_case) > 0 else 0
    
    with st.container(border=True):
        st.markdown("<h3 style='color: #EF4444;'>The Guaranteed Exit Profile</h3>", unsafe_allow_html=True)
        st.markdown("**Single + In-Office + Overtime + Poor Work-Life Balance**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Turnover Rate for this Group", f"{worst_case_rate:.1f}%")
        m2.metric("Company Average", f"{company_avg_attrition * 100:.1f}%")
        m3.metric("Employees At Risk Right Now", f"{len(worst_case):,}")
        
    st.info("**Insight:** We have nearly 1,000 people who fit this exact profile. They are quitting at a massive 87% rate.")
    st.error("**Action:** Freeze overtime for these 979 people today. If you do not adjust their workload, 850 of them will quit by December.")

    st.divider()

    st.markdown("### Q10: What Moves the Needle Most?")
    st.markdown("If we can only fix *one* thing next quarter, where do we get the highest return on investment?")
    
    drivers = ['Remote Work Status', 'work_life_balance', 'job_satisfaction']
    impact_data = []
    for d in drivers:
        rates = df.groupby(d, observed=True)['left_numeric'].mean()
        spread = (rates.max() - rates.min()) * 100
        impact_data.append({'Driver': d.replace('_', ' ').title(), 'Impact Spread (%)': spread})
        
    impact_df = pd.DataFrame(impact_data).sort_values('Impact Spread (%)', ascending=False)
    
    fig = px.bar(impact_df, x='Impact Spread (%)', y='Driver', orientation='h', 
                 text_auto='.1f', color_discrete_sequence=[brand_color])
    fig.update_layout(title="<b>The Biggest Drivers of Retention (Max vs Min Turnover Rates)</b>", 
                      xaxis_title="Difference in Turnover Rate (%)", yaxis_title="Factor")
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    st.info("**Insight:** Flexibility stops turnover better than job satisfaction. Where and how much people work matters most.")
    st.error("**Action:** Launch a 3-day work-from-home policy for all office workers next week. It costs nothing and will save over 1,500 employees from quitting this year.")

    st.divider()


    st.markdown("### A Final Word: Implementation & Next Steps")
    st.warning("**Disclaimer:** The data exposes clear, deep-rooted problems within our work environment. However, do not execute all these recommendations at once. Roll them out one by one. After each action, we must gather fresh data to measure the exact impact, validate our findings, and adjust our strategy before moving to the next phase.")


pg = st.navigation([
    st.Page(page_overview, title="Overview & Main Leaks"),
    st.Page(page_demographics, title="Who is Leaving?"),
    st.Page(page_environment, title="Burnout & Flexibility"),
    st.Page(page_career, title="Money & Career Growth"),
    st.Page(page_strategy, title="Final Strategy Plan")
])

pg.run()
