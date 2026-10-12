import json
from pathlib import Path
from collections import defaultdict
import pandas as pd
import streamlit as st

st.set_page_config(page_title='GameIQ | Film Intelligence', page_icon='🏈', layout='wide')
DATA=Path(__file__).parent/'plays.json'
FIELDS=['play_id','quarter','clock','down','distance','offense','formation','motion','play_type','target_player','tell','outcome','notes']

def load():
    try:
        data=json.loads(DATA.read_text(encoding='utf-8'))
        return data if isinstance(data,list) else []
    except (FileNotFoundError,json.JSONDecodeError): return []
def save(rows): DATA.write_text(json.dumps(rows,indent=2),encoding='utf-8')

def insights(rows):
    findings=[]
    def add(title,subset,description,counter):
        n=len(subset)
        if n>=3:
            findings.append({'Finding':title,'Evidence':f'{n} tagged plays','Observation':description,'Possible adjustment':counter,'Play IDs':', '.join(str(r['play_id']) for r in subset)})
    groups=defaultdict(list)
    for r in rows:
        if r.get('tell','None')!='None' and r.get('target_player','').strip():
            groups[(r['target_player'].strip().lower(),r['tell'])].append(r)
    for (player,tell),subset in groups.items():
        add(f'{player.title()}: repeated {tell.lower()}',subset,f'This player was tagged with “{tell}” on {len(subset)} plays. Verify against film and historical baselines.', 'Review the associated clips; test a counter concept only if the tell reliably predicts the play.')
    formations=defaultdict(list)
    for r in rows: formations[r['formation']].append(r)
    for formation,subset in formations.items():
        if len(subset)<4: continue
        counts=pd.Series([r['play_type'] for r in subset]).value_counts()
        kind,num=counts.index[0],int(counts.iloc[0])
        if num/len(subset)>=.7:
            add(f'{formation}: {kind.lower()} tendency',subset,f'{num}/{len(subset)} tagged plays ({num/len(subset):.0%}) were {kind.lower()} plays.', 'Consider a formation-specific response, while checking down, distance, score and game situation.')
    motions=defaultdict(list)
    for r in rows:
        if r['motion']!='None': motions[(r['motion'],r['play_type'])].append(r)
    for (motion,kind),subset in motions.items():
        add(f'{motion} motion + {kind.lower()}',subset,f'This combination appeared {len(subset)} times.', 'Review defensive alignment and response to motion before choosing a counter.')
    return sorted(findings,key=lambda x:int(x['Evidence'].split()[0]),reverse=True)[:5]

st.title('🏈 GameIQ')
st.caption('Film Intelligence • Local prototype v0.1 • Observations are human-tagged; findings are rule-based, not autonomous video AI.')
rows=load()
tab1,tab2,tab3=st.tabs(['🎬 Film & tag plays','📊 Tendencies','🧠 Halftime report'])
with tab1:
    clip=st.file_uploader('Upload an MP4 game clip',type=['mp4','mov','m4v'])
    if clip: st.video(clip)
    else: st.info('Upload a clip to watch it while tagging. Video is not automatically saved or analyzed.')
    st.subheader('Tag an observed play')
    with st.form('play_form',clear_on_submit=True):
        a,b,c=st.columns(3)
        with a:
            quarter=st.selectbox('Quarter',[1,2,3,4]); clock=st.text_input('Game clock (e.g. 08:21)'); down=st.selectbox('Down',[1,2,3,4]); distance=st.number_input('Yards to gain',1,99,10)
        with b:
            offense=st.text_input('Offense/team'); formation=st.selectbox('Formation',['Shotgun','Pistol','Under center','Empty','Other']); motion=st.selectbox('Motion',['None','Jet','Orbit','Shift','Other']); play_type=st.selectbox('Play type',['Run','Pass','Screen','RPO','Other'])
        with c:
            target_player=st.text_input('Player name or number'); tell=st.selectbox('Observed tell',['None','Early hip turn','Stance change','Weight shift','Early first step','Slow get-off','Overreaction to motion','Other']); outcome=st.text_input('Outcome (e.g. 6 yards)'); notes=st.text_area('Evidence / notes',height=90)
        submitted=st.form_submit_button('Save tagged play',type='primary')
        if submitted:
            row=dict(zip(FIELDS,[max([int(r.get('play_id',0)) for r in rows],default=0)+1,quarter,clock,down,int(distance),offense,formation,motion,play_type,target_player,tell,outcome,notes]))
            rows.append(row);save(rows);st.success(f'Saved play #{row["play_id"]}.');st.rerun()
    if rows:
        st.subheader(f'Saved plays ({len(rows)})')
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.download_button('Export plays as CSV',pd.DataFrame(rows).to_csv(index=False).encode(),'gameiq_plays.csv','text/csv')
        with st.expander('Delete a play'):
            selected=st.selectbox('Play ID',[r['play_id'] for r in rows]);
            if st.button('Delete selected play'):
                save([r for r in rows if r['play_id']!=selected]);st.rerun()
with tab2:
    if not rows: st.info('Tag some plays to see tendency statistics.')
    else:
        df=pd.DataFrame(rows)
        a,b,c=st.columns(3)
        a.metric('Tagged plays',len(rows));b.metric('Players tagged',df['target_player'].replace('',pd.NA).dropna().nunique());c.metric('Plays with tells',(df['tell']!='None').sum())
        st.subheader('Play types');st.bar_chart(df['play_type'].value_counts())
        st.subheader('Formation vs. play type');st.dataframe(pd.crosstab(df['formation'],df['play_type']),use_container_width=True)
        st.subheader('Observed player tells');st.dataframe(df[df['tell']!='None'][['play_id','target_player','tell','formation','play_type','notes']],hide_index=True,use_container_width=True)
with tab3:
    st.subheader('Top five candidate findings')
    st.warning('Exploratory observations only. Repeated tags are not proof of a predictive tell. Validate each finding against video, opponent history, and game context.')
    findings=insights(rows)
    if not findings: st.info('Add at least 3 matching player-tell or motion tags, or 4 plays from a formation with a 70%+ dominant play type.')
    for i,f in enumerate(findings,1):
        with st.container(border=True):
            st.markdown(f'### {i}. {f["Finding"]}')
            st.caption(f'{f["Evidence"]} • Play IDs: {f["Play IDs"]}')
            st.write(f['Observation']);st.markdown('**Possible adjustment:** '+f['Possible adjustment'])
    if findings: st.download_button('Download halftime report (JSON)',json.dumps(findings,indent=2).encode(),'gameiq_halftime_report.json','application/json')
