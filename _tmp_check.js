
  let currentIndex=0, totalRows=0, currentRow={}, resumeIndex=0, sidebarVisible=true, allPreviewData=[], currentUser='';
  const PREVIEW_COLS=["Company","Website","Lead Ranking","No. of Employees","Company Industry","First Name","Last Name","Title","Email","Phone","Alt. Contact Info","Alternate Phone","Street","City","State","Zip Code","Timezone","Validated By","Validated Date","Notes"];

  // Check login state on load
  fetch('/me').then(r=>r.json()).then(data=>{
    if(data.logged_in){
      currentUser = data.username;
      showApp();
    } else {
      showLogin();
    }
  });

  function showLogin(){
    document.getElementById('loginScreen').style.display='flex';
    document.getElementById('homeScreen').style.display='none';
    document.getElementById('uploadScreen').style.display='none';
    document.getElementById('validatorScreen').style.display='none';
    document.getElementById('previewScreen').style.display='none';
    document.getElementById('doneScreen').style.display='none';
    document.getElementById('tabBtns').style.display='none';
    document.getElementById('sidebarToggle').style.display='none';
    document.getElementById('userChip').style.display='none';
  }

  function showApp(){
    document.getElementById('loginScreen').style.display='none';
    document.getElementById('userChip').style.display='block';
    document.getElementById('validatedBy').value=currentUser;
    goHome();
  }

  function doLogin(){
    const username=document.getElementById('loginUser').value.trim();
    const password=document.getElementById('loginPass').value;
    fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})})
      .then(r=>r.json()).then(data=>{
        if(data.ok){
          currentUser=data.username;
          document.getElementById('loginErr').style.display='none';
          showApp();
        } else {
          document.getElementById('loginErr').style.display='block';
        }
      });
  }

  function doLogout(){
    fetch('/logout',{method:'POST'}).then(()=>{
      currentUser='';
      goHome();
      showLogin();
    });
  }

  document.getElementById('loginPass').addEventListener('keydown',function(e){
    if(e.key==='Enter') doLogin();
  });

  function loadHistory(){
    fetch('/files').then(r=>{
      if(!r.ok){
        if(r.status===401){
          showLogin();
          return null;
        }
        throw new Error('files request failed');
      }
      return r.json();
    }).then(data=>{
      if(!data) return;
      const grid = document.getElementById('historyGrid');
      if(!data.files || data.files.length === 0){
        grid.innerHTML='<div class="hc-empty">No files yet. Upload one to get started.</div>';
        return;
      }
      grid.innerHTML='';
      data.files.forEach(f=>{
        const pct = f.total > 0 ? Math.round((f.done/f.total)*100) : 0;
        const card = document.createElement('div');
        card.className = 'history-card';
        card.innerHTML = `<div class="hc-name" title="${f.filename}">${f.filename}</div>
          <div class="hc-bar-wrap"><div class="hc-bar" style="width:${pct}%"></div></div>
          <div class="hc-meta"><span>${f.done} / ${f.total} validated</span><span>${f.modified}</span></div>`;
        card.onclick = () => openDraft(f.key);
        grid.appendChild(card);
      });
    }).catch(()=>{
      const grid = document.getElementById('historyGrid');
      grid.innerHTML='<div class="hc-empty">Unable to load files.</div>';
    });
  }

  function openDraft(key){
    showSpinner(true);
    fetch(`/open/${key}`).then(r=>r.json()).then(data=>{
      showSpinner(false);
      if(data.error){ alert(data.error); return; }
      totalRows=data.total; resumeIndex=data.resume_index||0;
      showValidatorScreen();
      loadSidebar(); loadRow(resumeIndex);
    });
  }

  function goHome(){
    document.getElementById('homeScreen').style.display='flex';
    document.getElementById('validatorScreen').style.display='none';
    document.getElementById('previewScreen').style.display='none';
    document.getElementById('doneScreen').style.display='none';
    document.getElementById('tabBtns').style.display='none';
    document.getElementById('sidebarToggle').style.display='none';
    document.getElementById('progressText').textContent='';
    document.getElementById('progressBar').style.width='0%';
    loadHistory();
  }

  function showValidatorScreen(){
    document.getElementById('homeScreen').style.display='none';
    document.getElementById('uploadScreen').style.display='none';
    document.getElementById('validatorScreen').style.display='flex';
    document.getElementById('tabBtns').style.display='flex';
    document.getElementById('sidebarToggle').style.display='block';
  }

function selectRank(val) {
    document.getElementById('LeadRanking').value = val;
    document.querySelectorAll('.rank-btn').forEach(b => b.classList.remove('selected'));
    document.querySelectorAll('.rank-btn').forEach(b => { if(b.textContent.trim()===val) b.classList.add('selected'); });
    document.getElementById('rankRequired').style.display = 'none';
  }

  function switchTab(tab){
    document.querySelectorAll('.tab-btn').forEach((b,i)=>b.classList.toggle('active',(tab==='validate'&&i===0)||(tab==='preview'&&i===1)));
    document.getElementById('validatorScreen').style.display=tab==='validate'?'flex':'none';
    document.getElementById('previewScreen').style.display=tab==='preview'?'flex':'none';
    document.getElementById('sidebarToggle').style.display=tab==='validate'?'block':'none';
    if(tab==='preview') loadPreviewTable();
  }

  function toggleSidebar(){
    sidebarVisible=!sidebarVisible;
    document.getElementById('sidebar').classList.toggle('hidden',!sidebarVisible);
    document.getElementById('sidebarToggle').style.display=sidebarVisible?'none':'block';
  }

  function uploadFile(input){
    const file=input.files[0]; if(!file) return;
    const fd=new FormData(); fd.append("file",file);
    showSpinner(true);
    fetch("/upload",{method:"POST",body:fd}).then(r=>r.json()).then(data=>{
      if(data.error){alert(data.error);showSpinner(false);return;}
      totalRows=data.total; resumeIndex=data.resume_index||0;
      showValidatorScreen();
      loadSidebar(); loadRow(resumeIndex);
    });
  }

  function loadRow(idx){
    showSpinner(true);
    fetch(`/row/${idx}`).then(r=>r.json()).then(data=>{
      showSpinner(false);
      if(data.done){showDone();return;}
      currentRow=data.row; currentIndex=data.index; totalRows=data.total;
      renderRow(data.row,data.validations,data.suggested_rank,data.rank_reason);
      updateProgress(); highlightSidebar(idx);
    });
  }

  function loadSidebar(){
    fetch('/progress').then(r=>r.json()).then(data=>{
      if(!data.rows) return;
      totalRows = data.total;
      const list=document.getElementById('sidebarList'); list.innerHTML='';
      data.rows.forEach(r=>{
        const d=document.createElement('div');
        d.className='sb-item'+(r.done?' done':'')+(r.rank?' rank-'+r.rank:'');
        d.id='sitem-'+r.index;
        d.innerHTML=`<div class="sb-dot ${r.done?'d-done':'d-pend'}"></div><div style="flex:1;min-width:0"><div class="sb-co" title="${r.company}">${r.company||'(no name)'}</div><div class="sb-meta">${r.rank?`<span class="rank-badge rank-${r.rank}" style="font-size:0.55rem;padding:1px 5px">${r.rank}</span>`:''} ${r.done?'· '+(r.validated_by||''):''}</div></div>`;
        d.onclick=()=>loadRow(r.index);
        list.appendChild(d);
      });
      document.getElementById('sidebarStats').textContent=`${data.done_count} / ${data.total}`;
    }).catch(()=>{});
  }

  function highlightSidebar(idx){
    document.querySelectorAll('.sb-item').forEach(el=>el.classList.remove('active'));
    const el=document.getElementById('sitem-'+idx);
    if(el){el.classList.add('active');el.scrollIntoView({block:'nearest'});}
  }

  function loadPreviewTable(){
    fetch('/progress').then(r=>r.json()).then(data=>{
      if(!data.rows_full) return;
      allPreviewData=data.rows_full||[];
      renderTable(allPreviewData);
      document.getElementById('previewCount').textContent=`${data.done_count} of ${data.total} validated`;
    });
  }

  function renderTable(rows){
    document.getElementById('previewHead').innerHTML='<tr>'+['#',...PREVIEW_COLS,'Status'].map(c=>`<th>${c}</th>`).join('')+'</tr>';
    const body=document.getElementById('previewBody'); body.innerHTML='';
    rows.forEach(r=>{
      const tr=document.createElement('tr');
      const rank=r['Lead Ranking']||'';
      tr.className=rank?'row-'+rank:'';
      tr.onclick=()=>{switchTab('validate');setTimeout(()=>loadRow(r._index),50);};
      let cells=`<td>${r._index+1}</td>`;
      PREVIEW_COLS.forEach(col=>{
        const val=r[col]||'';
        cells+=col==='Lead Ranking'&&val?`<td><span class="rank-badge rank-${val}">${val}</span></td>`:`<td title="${val}">${val}</td>`;
      });
      cells+=`<td>${r._done?'✓':'—'}</td>`;
      tr.innerHTML=cells; body.appendChild(tr);
    });
  }

  function filterTable(){
    const q=document.getElementById('previewSearch').value.toLowerCase();
    renderTable(allPreviewData.filter(r=>PREVIEW_COLS.some(col=>(r[col]||'').toLowerCase().includes(q))));
  }

  function companyValueFromRow(row){
    const direct = row['Company'] || row['Company Name'] || row['Company name'] || row['Organization'] || row['Organization Name'] || row['Account Name'] || row['Account'] || row['Client'];
    if(direct && String(direct).trim() && String(direct).trim().toLowerCase() !== 'nan') return String(direct).trim();
    const ws = String(row['Website'] || '').trim();
    if(ws){
      try {
        const host = new URL(ws.startsWith('http') ? ws : 'https://' + ws).hostname.replace(/^www\./i, '');
        if(host) return host;
      } catch(e) {
        const value = ws.replace(/^https?:\/\//i, '').replace(/^www\./i, '').split('/')[0];
        if(value) return value;
      }
    }
    return '';
  }

  function renderRow(row,v,suggested_rank,rank_reason){
    const co = companyValueFromRow(row);
    document.getElementById("companyName").textContent=co || "—";
    document.getElementById("CompanyInput").value=co || "";
    const ws=row["Website"]||"";
    const wl=document.getElementById("websiteLink"); wl.textContent=ws; wl.href=ws.startsWith("http")?ws:"https://"+ws;
    document.getElementById("Industry").value=row["Company Industry"]||"";
    document.getElementById("FirstName").value=row["First Name"]||"";
    document.getElementById("LastName").value=row["Last Name"]||"";
    document.getElementById("Title").value=row["Title"]||"";
    document.getElementById("Email").value=row["Email"]||"";
    document.getElementById("Phone").value=row["Phone"]||"";
    document.getElementById("AltContact").value=row["Alt. Contact Info"]||"";
    document.getElementById("AltPhone").value=row["Alternate Phone"]||"";
    document.getElementById("Street").value=row["Street"]||"";
    document.getElementById("City").value=row["City"]||"";
    document.getElementById("State").value=row["State"]||"";
    document.getElementById("ZipCode").value=row["Zip Code"]||"";
    document.getElementById("Timezone").value=row["Timezone"]||"";
    document.getElementById("NumEmployees").value=row["No. of Employees"]||"";
    document.getElementById("Website").value=ws;
    document.getElementById("Notes").value=row["Notes"]||"";

    // Reset rank buttons — no default selection
    document.getElementById('LeadRanking').value='';
    document.querySelectorAll('.rank-btn').forEach(b=>b.classList.remove('selected'));
    document.getElementById('rankRequired').style.display='none';

    // Show suggestion but don't auto-select
    document.getElementById('rankSuggested').textContent = suggested_rank ? `Suggested: ${suggested_rank}` : '';
    document.getElementById('rankReason').textContent=rank_reason||"";

    // If row already has a saved rank, select it
    const savedRank = row["Lead Ranking"]||"";
    if(savedRank) selectRank(savedRank);

    setHint("hint_phone","f_Phone",v.phone);
    setHint("hint_email","f_Email",v.email);
    setHint("hint_website","f_Website",v.website);
    setHint("hint_title","f_Title",v.title);

    const ap=row["Alternate Phone"]||"";
    if(ap.trim()){
      const d=ap.replace(/\D/g,'').replace(/^1(\d{10})$/,'$1');
      const TF=[800,833,844,855,866,877,888];
      const ok=d.length===10&&!TF.includes(parseInt(d.substring(0,3)));
      setHint("hint_altphone","f_AltPhone",{valid:ok,msg:ok?"Valid":"Invalid"});
    } else { document.getElementById("hint_altphone").textContent=""; document.getElementById("f_AltPhone").className="f"; }

    const name=`${row["First Name"]||""} ${row["Last Name"]||""}`.trim();
    const co = companyValueFromRow(row);
    const companySearch = co || (ws ? (function(){try{return new URL(ws.startsWith('http')?ws:'https://'+ws).hostname.replace(/^www\./i,'');}catch(e){return '';}}()) : '');
    document.getElementById("btn_google").href=`https://www.google.com/search?q=${encodeURIComponent((companySearch || co)+' '+name+' phone number')}`;
    document.getElementById("btn_linkedin").href=`https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(name+' '+(companySearch || co))}`;
    document.getElementById("btn_apollo").href=`https://app.apollo.io/#/people?q_organization_name=${encodeURIComponent(companySearch || co)}&q_keywords=${encodeURIComponent(name)}`;
    document.getElementById("btn_contactout").href=`https://contactout.com/search?name=${encodeURIComponent(name)}&company=${encodeURIComponent(companySearch || co)}`;
    document.getElementById("btn_linkedin_company").href=`https://www.linkedin.com/search/results/companies/?keywords=${encodeURIComponent(companySearch || co)}`;
    document.getElementById("btn_google_company").href=`https://www.google.com/search?q=${encodeURIComponent(companySearch || co)}`;
    document.getElementById("btn_apollo_company").onclick=function(e){
      e.preventDefault();
      const apolloUrl=`https://app.apollo.io/#/companies?q_organization_name=${encodeURIComponent(companySearch || co)}`;
      if(ws) openLink(ws.startsWith("http")?ws:"https://"+ws);
      openLink(apolloUrl);
    };
    document.getElementById("btn_apollo_company").setAttribute('href', `https://app.apollo.io/#/companies?q_organization_name=${encodeURIComponent(companySearch || co)}`);
    const addr=`${row["Street"]||""}, ${row["City"]||""}, ${row["State"]||""} ${row["Zip Code"]||""}`;
    document.getElementById("btn_maps").href=`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}`;

    const ah=document.getElementById("hint_address");
    ah.textContent="Address: "+v.address.msg; ah.className="hint "+(v.address.valid?"ok":"err");
    document.getElementById("f_Street").className="f "+(v.address.valid?"fv":"fi");
    checkTimezone();
    updateLinkHandlers();
  }

  function setHint(hId,fId,v){
    const el=document.getElementById(hId);
    if(el){el.textContent=v.msg;el.className="hint "+(v.valid?"ok":"err");}
    if(fId){const f=document.getElementById(fId);if(f)f.className="f "+(v.valid?"fv":"fi");}
  }

  function saveAndNext(){
    const rank=document.getElementById('LeadRanking').value;
    if(!rank){
      document.getElementById('rankRequired').style.display='inline';
      return;
    }
    if(!document.getElementById('NumEmployees').value.trim()){
      document.getElementById('NumEmployees').style.borderColor='#ea4335';
      document.getElementById('NumEmployees').focus();
      return;
    }
    const vb=document.getElementById("validatedBy").value.trim();
    const today=new Date().toLocaleDateString("en-US",{month:"2-digit",day:"2-digit",year:"numeric"});
    const payload={
      "Company":document.getElementById("CompanyInput").value.trim() || document.getElementById("companyName").textContent.trim(),
      "First Name":document.getElementById("FirstName").value,
      "Last Name":document.getElementById("LastName").value,
      "Title":document.getElementById("Title").value,
      "Email":document.getElementById("Email").value,
      "Phone":document.getElementById("Phone").value,
      "Alt. Contact Info":document.getElementById("AltContact").value,
      "Alternate Phone":document.getElementById("AltPhone").value,
      "Street":document.getElementById("Street").value,
      "City":document.getElementById("City").value,
      "State":document.getElementById("State").value,
      "Zip Code":document.getElementById("ZipCode").value,
      "Timezone":document.getElementById("Timezone").value,
      "No. of Employees":document.getElementById("NumEmployees").value,
      "Company Industry":document.getElementById("Industry").value,
      "Website":document.getElementById("Website").value,
      "Notes":document.getElementById("Notes").value,
      "Lead Ranking":rank,
      "Validated By":vb,"Validated Date":today
    };
    fetch(`/save/${currentIndex}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})
      .then(r=>r.json()).then(data=>{
        loadSidebar();
        loadRow(currentIndex+1);
      });
  }

  const STATE_TZ = {
    'AL':'CST','AK':'AKST','AZ':'MST','AR':'CST','CA':'PST','CO':'MST','CT':'EST','DE':'EST',
    'FL':'EST','GA':'EST','HI':'HST','ID':'MST','IL':'CST','IN':'EST','IA':'CST','KS':'CST',
    'KY':'EST','LA':'CST','ME':'EST','MD':'EST','MA':'EST','MI':'EST','MN':'CST','MS':'CST',
    'MO':'CST','MT':'MST','NE':'CST','NV':'PST','NH':'EST','NJ':'EST','NM':'MST','NY':'EST',
    'NC':'EST','ND':'CST','OH':'EST','OK':'CST','OR':'PST','PA':'EST','RI':'EST','SC':'EST',
    'SD':'CST','TN':'CST','TX':'CST','UT':'MST','VT':'EST','VA':'EST','WA':'PST','WV':'EST',
    'WI':'CST','WY':'MST','DC':'EST'
  };

  function checkTimezone(){
    const tz = document.getElementById('Timezone').value.trim().toUpperCase();
    const state = document.getElementById('State').value.trim().toUpperCase();
    const hint = document.getElementById('hint_timezone');
    if(!tz || !state){ hint.textContent=''; return; }
    const expected = STATE_TZ[state];
    if(!expected){ hint.textContent=''; return; }
    if(tz === expected || tz.toUpperCase().includes(expected)){
      hint.textContent='✓ Matches '+expected; hint.className='hint ok';
    } else {
      hint.textContent='Expected '+expected+' for '+state; hint.className='hint err';
    }
  }

  document.getElementById('Timezone').addEventListener('input', checkTimezone);
  document.getElementById('State').addEventListener('input', checkTimezone);

  document.getElementById('NumEmployees').addEventListener('input',function(){
    this.style.borderColor='';
  });

  function openLink(url) {
    window.open(url, '_blank');
  }

  // Alt contact buttons use live input value at click time
  ['btn_linkedin_alt','btn_contactout_alt','btn_apollo_alt'].forEach(id => {
    document.getElementById(id).addEventListener('click', function(e) {
      e.preventDefault();
      const an = document.getElementById('AltContact').value.split('-')[0].trim();
      const co = document.getElementById('companyName').textContent.trim();
      const urls = {
        btn_linkedin_alt:   `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(an)}`,
        btn_contactout_alt: `https://contactout.com/search?name=${encodeURIComponent(an)}&company=${encodeURIComponent(co)}`,
        btn_apollo_alt:     `https://app.apollo.io/#/people?q_organization_name=${encodeURIComponent(co)}&q_keywords=${encodeURIComponent(an)}`
      };
      openLink(urls[id]);
    });
  });

  function updateLinkHandlers() {
    document.querySelectorAll('a.sb:not(#btn_linkedin_alt):not(#btn_contactout_alt):not(#btn_apollo_alt)').forEach(a => {
      a.onclick = function(e) {
        e.preventDefault();
        const url = this.getAttribute('href');
        if (url && url !== '#') openLink(url);
      };
    });
  }
  function deleteRow(){
    if(!confirm('Delete this row permanently?')) return;
    fetch(`/delete/${currentIndex}`,{method:'POST'}).then(r=>r.json()).then(data=>{
      totalRows=data.total;
      loadSidebar();
      loadRow(currentIndex < totalRows ? currentIndex : currentIndex - 1);
    });
  }

  function goBack(){if(currentIndex>0)loadRow(currentIndex-1);}

  function getCurrentPayload(){
    const rank=document.getElementById('LeadRanking').value;
    if(!rank) return null;
    const vb=document.getElementById("validatedBy").value.trim();
    const today=new Date().toLocaleDateString("en-US",{month:"2-digit",day:"2-digit",year:"numeric"});
    return {
      "Company":document.getElementById("CompanyInput").value.trim() || document.getElementById("companyName").textContent.trim(),
      "First Name":document.getElementById("FirstName").value,
      "Last Name":document.getElementById("LastName").value,
      "Title":document.getElementById("Title").value,
      "Email":document.getElementById("Email").value,
      "Phone":document.getElementById("Phone").value,
      "Alt. Contact Info":document.getElementById("AltContact").value,
      "Alternate Phone":document.getElementById("AltPhone").value,
      "Street":document.getElementById("Street").value,
      "City":document.getElementById("City").value,
      "State":document.getElementById("State").value,
      "Zip Code":document.getElementById("ZipCode").value,
      "Timezone":document.getElementById("Timezone").value,
      "No. of Employees":document.getElementById("NumEmployees").value,
      "Company Industry":document.getElementById("Industry").value,
      "Website":document.getElementById("Website").value,
      "Notes":document.getElementById("Notes").value,
      "Lead Ranking":rank,
      "Validated By":vb,"Validated Date":today
    };
  }

  function autoSave(){
    if(totalRows===0) return;
    const payload=getCurrentPayload();
    if(!payload) return;
    fetch(`/save/${currentIndex}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})
      .then(r=>r.json()).then(data=>{
        document.getElementById('sidebarStats').textContent=`${data.done_count} / ${totalRows}`;
      });
  }

  setInterval(autoSave, 30000);

  window.addEventListener('beforeunload', function(){
    const payload=getCurrentPayload();
    if(!payload) return;
    const blob=new Blob([JSON.stringify(payload)],{type:'application/json'});
    navigator.sendBeacon(`/save/${currentIndex}`, blob);
  });

  function updateProgress(){
    const pct=Math.round((currentIndex/totalRows)*100);
    document.getElementById("progressBar").style.width=pct+"%";
    document.getElementById("progressText").textContent=`${currentIndex+1} / ${totalRows}`;
  }

  function showDone(){
    document.getElementById("validatorScreen").style.display="none";
    document.getElementById("previewScreen").style.display="none";
    document.getElementById("doneScreen").style.display="flex";
    document.getElementById("sidebarToggle").style.display="none";
    document.getElementById("progressBar").style.width="100%";
    document.getElementById("progressText").textContent=`${totalRows} / ${totalRows}`;
    loadHistory();
  }

  function downloadFile(){window.location.href="/download";}
  function showSpinner(show){document.getElementById("spinner").className=show?"spinner on":"spinner";}
