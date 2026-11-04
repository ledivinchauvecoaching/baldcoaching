/* Imitation minimale de supabase-js pour les tests (stockage dans localStorage).
   Reproduit le cloisonnement RLS : chaque requête ne voit que les lignes de l'utilisateur connecté. */
(function(){
  const LS=k=>JSON.parse(localStorage.getItem(k)||"null"),SET=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
  const session=()=>LS("mock-session");
  const rows=()=>LS("mock-db")||[];
  let authCb=null;
  function q(table){
    const st={op:"select",filters:[],row:null};
    const run=()=>{
      const s=session();if(!s)return {data:null,error:{message:"non connecté"}};
      const uid=s.user.id;let all=rows();
      const match=r=>r.user_id===uid&&st.filters.every(([c,v])=>r[c]===v);
      if(st.op==="select")return {data:all.filter(match).map(r=>({doc_id:r.doc_id,data:r.data})),error:null};
      if(st.op==="upsert"){const r=st.row;if(r.user_id!==uid)return {data:null,error:{message:"RLS"}};all=all.filter(x=>!(x.user_id===r.user_id&&x.collection===r.collection&&x.doc_id===r.doc_id));all.push(JSON.parse(JSON.stringify(r)));SET("mock-db",all);return {data:null,error:null}}
      if(st.op==="delete"){SET("mock-db",all.filter(r=>!match(r)));return {data:null,error:null}}
    };
    const b={select(){st.op="select";return b},upsert(r){st.op="upsert";st.row=r;return b},delete(){st.op="delete";return b},
      eq(c,v){st.filters.push([c,v]);return b},then(ok,ko){return Promise.resolve().then(run).then(ok,ko)}};
    return b;
  }
  window.supabase={createClient(){return {
    auth:{
      async getSession(){return {data:{session:session()}}},
      onAuthStateChange(cb){authCb=cb;return {data:{subscription:{unsubscribe(){}}}}},
      async signInWithOtp({email}){SET("mock-last-otp",email);return {error:null}},
      async signInWithOAuth(){return {error:null}},
      async signOut(){localStorage.removeItem("mock-session");authCb&&authCb("SIGNED_OUT",null);return {error:null}}
    },
    from:q,
    channel(){const c={on(){return c},subscribe(){return c}};return c}
  }}};
  window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock-anon"};
})();
