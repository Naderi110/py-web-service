if(currentDomain){
              $('#domain-value').textContent=currentDomain;
              $('#domain-value').style.color='var(--green)';
              $('#domain-clear-btn').style.display='block';
            }else{
              $('#domain-value').textContent=renderDomain+' (default)';
              $('#domain-value').style.color='var(--text2)';
              $('#domain-clear-btn').style.display='none';
            }
          }catch(e){}
        }

        async function saveDomain(){
          const domain=$('#domain-input').value.trim();
          if(!domain){toast('Enter a domain',true);return;}
          try{
            const r=await fetch('/api/domain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({domain})});
            if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.detail||'Error');}
            toast('Domain saved');
            $('#domain-input').value='';
            await loadDomain();
            await loadLinks();
          }catch(e){toast(e.message,true)}
        }

        async function clearDomain(){
          try{
            await fetch('/api/domain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({domain:''})});
            toast('Domain cleared');
            await loadDomain();
            await loadLinks();
          }catch(e){toast('Error',true)}
        }

        function renderAddresses(){
          const list=$('#address-list');if(!list)return;
          if(!allAddresses.length){list.innerHTML='<div style="color:var(--text3);font-size:12px;padding:8px 0">No addresses added</div>';return;}
          list.innerHTML=allAddresses.map((a,i)=>`
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px">
              <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:14px">🌐</span>
                <div>
                  <div style="font-size:13px;font-weight:600;color:var(--text)">${esc(a)}</div>
                  <div style="font-size:10px;color:var(--text3)">Address #${i+1}</div>
                </div>
              </div>
              <button class="btn btn-danger btn-sm" onclick="deleteAddress(${i})" style="padding:4px 10px">x</button>
            </div>
          `).join('');
        }

        function showAddAddressModal(){$('#new-address').value='';$('#add-address-modal').classList.add('show')}

        async function addAddresses(){
          const text=$('#new-address').value.trim();
          if(!text){toast('Enter at least one IP or domain',true);return;}
          const lines=text.split('\\n').map(l=>l.trim()).filter(l=>l);
          let added=0;let errors=0;
          for(const addr of lines){
            if(!/^[a-zA-Z0-9\\-_. ]+$/.test(addr)){errors++;continue;}
            try{
              const r=await fetch('/api/addresses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({address:addr})});
              if(r.ok)added++;else errors++;
            }catch(e){errors++;}
          }
          if(added>0)toast(`Added ${added} address(es)`);
          if(errors>0)toast(`${errors} failed`,true);
          if(added>0){$('#add-address-modal').classList.remove('show');await loadAddresses();}
        }

        async function deleteAddress(index){
          if(!confirm('Delete this address?'))return;
          try{
            const r=await fetch(`/api/addresses/${index}`,{method:'DELETE'});
            if(!r.ok)throw new Error();
            toast('Deleted');
            await loadAddresses();
          }catch(e){toast('Error',true)}
        }

        let chartLabels=[];let chartData=[];
        function initChart(){
          const ctx=document.getElementById('trafficChart');if(!ctx)return;
          trafficChart=new Chart(ctx,{type:'bar',data:{labels:[],datasets:[{label:'MB',data:[],backgroundColor:'rgba(220,38,38,0.7)',borderColor:'#dc2626',borderWidth:1,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:'rgba(255,255,255,0.3)',font:{size:10}}},y:{grid:{color:'rgba(255,255,255,0.05)'},ticks:{color:'rgba(255,255,255,0.3)',font:{size:10},callback:v=>v+' MB'},beginAtZero:true}}}});
        }
        initChart();
        function updateChart(){
          if(!trafficChart||!statsData.hourly_traffic)return;
          const ht=statsData.hourly_traffic;
          const sorted=Object.entries(ht).sort((a,b)=>a[0].localeCompare(b[0])).slice(-12);
          const labels=sorted.map(e=>e[0]);
          const data=sorted.map(e=>Math.round(e[1]/1048576));
          trafficChart.data.labels=labels;trafficChart.data.datasets[0].data=data;
          trafficChart.update();
        }
</script>
</body>
</html>"""

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get(Config.SESSION_COOKIE)
    async with state.sessions_lock:
        if token and state.sessions.get(token, 0) > time.time():
            return RedirectResponse(url="/dashboard")
    return HTMLResponse(content=LOGIN_HTML)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    token = request.cookies.get(Config.SESSION_COOKIE)
    async with state.sessions_lock:
        if not token or state.sessions.get(token, 0) < time.time():
            return RedirectResponse(url="/login")
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)