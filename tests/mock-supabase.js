/* Imitation minimale de supabase-js pour les tests (stockage dans localStorage).
   Reproduit les règles de la base :
   - sans "mock-roles" : ancienne base (schema.sql seul), chacun ne voit que ses lignes, pas de fonctions RPC ;
   - avec "mock-roles" : espace coach (02_espace_coach.sql) : membres, invitations, lecture coach,
     écriture coach limitée aux séances prévues et commentaires. */
(function(){
  const LS=k=>JSON.parse(localStorage.getItem(k)||"null"),SET=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
  const session=()=>LS("mock-session");
  const rows=()=>LS("mock-db")||[];
  const coachMode=()=>LS("mock-roles")!==null;
  const isCoach=u=>(LS("mock-roles")||[]).includes(u);
  const links=()=>LS("mock-coaching")||[];
  const isMember=u=>!coachMode()||isCoach(u)||links().some(l=>l.client_id===u&&l.actif);
  const coaches=(c,cl)=>coachMode()&&isCoach(c)&&links().some(l=>l.client_id===cl&&l.coach_id===c&&l.actif);
  const COACH_W=["prevues","commentaires"];
  const coachDoc=r=>r.collection==="reglages"&&r.doc_id==="coach";
  const coachW=r=>COACH_W.includes(r.collection)||(coachMode()&&coachDoc(r));
  const canRead=(u,r)=>r.user_id===u||coaches(u,r.user_id);
  const canWrite=(u,r)=>(r.user_id===u&&isMember(u)&&!(coachMode()&&coachDoc(r)))||(coachW(r)&&coaches(u,r.user_id));
  const canDel=(u,r)=>(r.user_id===u&&!(coachMode()&&coachDoc(r)))||(coachW(r)&&coaches(u,r.user_id));
  let authCb=null;
  function q(table){
    const st={op:"select",filters:[],row:null};
    const run=()=>{
      const s=session();if(!s)return {data:null,error:{message:"non connecté"}};
      const uid=s.user.id;let all=rows();
      const match=r=>st.filters.every(([c,v])=>r[c]===v);
      if(st.op==="select")return {data:all.filter(r=>match(r)&&canRead(uid,r)).map(r=>({doc_id:r.doc_id,data:r.data})),error:null};
      if(st.op==="upsert"){const r=st.row;if(!canWrite(uid,r))return {data:null,error:{message:"new row violates row-level security policy"}};all=all.filter(x=>!(x.user_id===r.user_id&&x.collection===r.collection&&x.doc_id===r.doc_id));all.push(JSON.parse(JSON.stringify(r)));SET("mock-db",all);return {data:null,error:null}}
      if(st.op==="delete"){SET("mock-db",all.filter(r=>!(match(r)&&canDel(uid,r))));return {data:null,error:null}}
    };
    const b={select(){st.op="select";return b},upsert(r){st.op="upsert";st.row=r;return b},delete(){st.op="delete";return b},
      eq(c,v){st.filters.push([c,v]);return b},then(ok,ko){return Promise.resolve().then(run).then(ok,ko)}};
    return b;
  }
  const tok=()=>Array.from({length:64},()=>"0123456789abcdef"[Math.floor(Math.random()*16)]).join("");
  const RPC={
    mon_statut(me){if(isCoach(me))return {role:"coach"};const l=links().find(x=>x.client_id===me);if(l&&l.actif)return {role:"client",depuis:l.depuis};if(l)return {role:"suspendu"};return {role:"aucun"}},
    creer_invitation(me,{p_note,p_email}){if(!isCoach(me))throw "reserve au coach";const e=String(p_email||"").trim().toLowerCase();if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e))throw "email invalide";const t=tok(),inv=LS("mock-invitations")||[];const x={token:t,coach_id:me,note:p_note||null,email:e,cree_le:new Date().toISOString(),expire_le:new Date(Date.now()+14*864e5).toISOString(),utilise_par:null};inv.push(x);SET("mock-invitations",inv);return {token:t,note:x.note,email:e,expire_le:x.expire_le}},
    mes_invitations(me){return (LS("mock-invitations")||[]).filter(x=>x.coach_id===me&&isCoach(me)&&!x.utilise_par&&new Date(x.expire_le)>new Date()).map(({token,note,email,cree_le,expire_le})=>({token,note,email,cree_le,expire_le}))},
    annuler_invitation(me,{p_token}){SET("mock-invitations",(LS("mock-invitations")||[]).filter(x=>!(x.token===p_token&&x.coach_id===me&&!x.utilise_par)));return null},
    accepter_invitation(me,{p_token}){if(isCoach(me))return {ok:false,raison:"coach"};const inv=LS("mock-invitations")||[],x=inv.find(i=>i.token===p_token);
      if(!x||x.utilise_par||new Date(x.expire_le)<new Date())return {ok:false,raison:"invalide"};
      const s=session();if(x.email&&String(s.user.email).toLowerCase()!==x.email)return {ok:false,raison:"autre_email"};const L=links().filter(l=>l.client_id!==me);L.push({client_id:me,coach_id:x.coach_id,client_email:s.user.email,client_nom:(s.user.user_metadata||{}).full_name||null,depuis:new Date().toISOString(),actif:true});SET("mock-coaching",L);
      x.utilise_par=me;SET("mock-invitations",inv);return {ok:true}},
    mes_clients(me){return isCoach(me)?links().filter(l=>l.coach_id===me).map(l=>({id:l.client_id,email:l.client_email,nom:l.client_nom,depuis:l.depuis,actif:l.actif})):[]},
    changer_client(me,{p_client,p_actif}){if(!isCoach(me))return null;SET("mock-coaching",links().map(l=>l.client_id===p_client&&l.coach_id===me?{...l,actif:p_actif}:l));return null}
  };
  async function rpc(name,args){
    const s=session();if(!s)return {data:null,error:{message:"permission denied"}};
    if(!coachMode()||!RPC[name])return {data:null,error:{code:"PGRST202",message:"Could not find the function"}};
    try{return {data:RPC[name](s.user.id,args||{}),error:null}}catch(e){return {data:null,error:{message:String(e)}}}
  }
  window.supabase={createClient(){return {
    auth:{
      async getSession(){return {data:{session:session()}}},
      onAuthStateChange(cb){authCb=cb;return {data:{subscription:{unsubscribe(){}}}}},
      async signInWithOtp({email}){
        /* crochet « inscription sur invitation » : une adresse inconnue sans invitation est refusée */
        if(coachMode()&&LS("mock-hook")&&!(LS("mock-known")||[]).includes(email)&&!(LS("mock-invitations")||[]).some(i=>i.email===String(email).toLowerCase()&&!i.utilise_par))
          return {error:{status:403,message:"Inscription reservee aux clients de bald.coaching : demande ton lien d'invitation a ton coach."}};
        SET("mock-last-otp",email);return {error:null}},
      async signInWithOAuth(){return {error:null}},
      async signOut(){localStorage.removeItem("mock-session");authCb&&authCb("SIGNED_OUT",null);return {error:null}}
    },
    from:q,rpc,
    channel(){const c={on(){return c},subscribe(){return c}};return c},
    removeChannel(){}
  }}};
  window.BALD_CONFIG={supabaseUrl:"https://mock.supabase.co",supabaseAnonKey:"mock-anon"};
})();
