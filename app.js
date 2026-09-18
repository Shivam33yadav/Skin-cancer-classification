/* ---------- figure interaction ---------- */
const FIG = {
  ak:{k:"Upper epidermis · in situ",t:"Actinic keratosis and Bowen's disease",d:"Damaged keratinocytes confined above the basement membrane. Nothing has crossed into the dermis, so nothing can spread. Left untreated, a proportion break through and become invasive squamous cell carcinoma."},
  scc:{k:"Epidermis · keratinocytes",t:"Squamous cell carcinoma",d:"Arises from the flat keratin-making cells in the middle and upper epidermis. Once through the basement membrane it can reach dermal lymphatics, which is why nodal spread is possible."},
  bcc:{k:"Basal layer",t:"Basal cell carcinoma",d:"Grows from the deepest row of the epidermis and from hair follicle stem cells. It burrows outward and downward through local tissue but almost never enters the bloodstream."},
  mel:{k:"Basal layer · melanocytes",t:"Melanoma",d:"Starts in the pigment cells scattered along the base of the epidermis. Its danger is measured by how far down it has travelled into the dermis — the Breslow scale on the right."},
  mcc:{k:"Dermo-epidermal junction",t:"Merkel cell carcinoma",d:"Arises near the touch-receptor cells at the base of the epidermis. Rare, fast, and often painless — a combination that delays diagnosis."}
};
const figread = document.getElementById('figread');
document.querySelectorAll('.pin').forEach(p=>{
  const act = ()=>{
    document.querySelectorAll('.pin').forEach(x=>x.classList.remove('sel'));
    p.classList.add('sel');
    const d = FIG[p.dataset.k];
    figread.innerHTML = '<span class="k">'+d.k+'</span><h4>'+d.t+'</h4><p>'+d.d+'</p>';
  };
  p.addEventListener('click',act);
  p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act();}});
});

/* ---------- nav active state ---------- */
const links = [...document.querySelectorAll('#tabs a')];
const secs = links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
const io = new IntersectionObserver(es=>{
  es.forEach(e=>{
    if(e.isIntersecting){
      links.forEach(l=>l.classList.remove('on'));
      const m = links.find(l=>l.getAttribute('href')==='#'+e.target.id);
      if(m && !m.classList.contains('check')) m.classList.add('on');
    }
  });
},{rootMargin:'-45% 0px -50% 0px'});
secs.forEach(s=>io.observe(s));

/* ---------- checker model ---------- */
const TYPES = [
 {id:'bcc',name:'Basal cell carcinoma',grp:'Keratinocyte carcinoma',
  blurb:'A slow-growing local cancer of the basal layer. Very rarely spreads, but keeps enlarging and destroys nearby tissue if left, so it still needs treating.',
  w:{look_pearly:4,look_sore:3,site_face:3,col_skin:2,col_white:2,sym_bleed:3,sym_crust:2,dur_long:2,dur_mid:1,dur_years_changed:1,size_growing:1,risk_fair:1,risk_outdoor:1,risk_prev:2,col_blackblue:1,bord_even:1,fitz_12:1,site_lips:1}},

 {id:'scc',name:'Squamous cell carcinoma',grp:'Keratinocyte carcinoma',
  blurb:'A firmer, faster keratinocyte cancer that is often tender. It can reach lymph nodes, especially on the lip and ear or in someone immunosuppressed.',
  w:{look_wart:4,look_scaly:3,look_sore:3,site_face:2,site_arms:2,site_lips:4,sym_pain:2,sym_crust:2,sym_bleed:2,size_growing:2,dur_mid:2,dur_long:1,risk_immuno:3,risk_outdoor:2,risk_prev:2,col_redpink:2,fitz_12:1}},

 {id:'ak',name:'Actinic keratosis',grp:'Pre-cancer, not yet cancer',
  blurb:'Sun-damaged patches that feel rougher than they look. Most never progress, but a small share turn into squamous cell carcinoma, so they are usually treated.',
  w:{look_scaly:4,site_face:3,site_arms:2,col_redpink:2,sym_none:1,dur_years:2,dur_long:2,risk_outdoor:3,risk_fair:2,fitz_12:2,size_small:1,sym_itch:1},
  neg:{look_sore:2,sym_bleed:1,look_fastnodule:2}},

 {id:'bowen',name:"Bowen's disease (SCC in situ)",grp:'Cancer confined to the surface',
  blurb:'Squamous cancer cells still trapped above the basement membrane. Looks like a stubborn patch of psoriasis or eczema that never responds to creams.',
  w:{look_patch:4,look_scaly:3,site_legs:3,col_redpink:3,dur_long:2,dur_years:2,bord_even:2,size_large:1,risk_outdoor:1}},

 {id:'ssm',name:'Superficial spreading melanoma',grp:'Melanoma',
  blurb:'The commonest melanoma. Spreads sideways first, which is what makes early detection possible — and why any change in an existing mole matters.',
  w:{look_flatpigment:4,look_darkraised:2,col_multi:4,bord_uneven:4,size_large:3,chg_color:3,chg_grew:3,site_trunk:3,site_legs:3,sym_itch:2,sym_bleed:2,risk_moles:2,risk_fam:3,risk_burns:2,dur_years_changed:3,dur_mid:2,col_blackblue:2},
  neg:{chg_none:3,col_uniform:2}},

 {id:'nm',name:'Nodular melanoma',grp:'Melanoma',
  blurb:'Grows downward from the start, so it gets thick fast. Often perfectly round and one colour, which means the ABCDE rule frequently misses it entirely.',
  w:{look_fastnodule:4,look_darkraised:3,col_blackblue:3,chg_raised:3,size_growing:3,sym_bleed:3,dur_new:3,dur_mid:2,site_trunk:2,site_face:1,bord_even:1,risk_fam:1},
  neg:{chg_none:3,dur_years:2}},

 {id:'lmm',name:'Lentigo maligna / LM melanoma',grp:'Melanoma',
  blurb:'A slowly widening stain on heavily sun-damaged skin, usually in older adults. Frequently written off as an age spot for a decade or more.',
  w:{look_flatpigment:4,site_face:4,dur_years:3,dur_years_changed:3,size_large:3,col_multi:2,bord_uneven:3,chg_grew:2,risk_outdoor:3,fitz_12:1}},

 {id:'alm',name:'Acral lentiginous melanoma',grp:'Melanoma',
  blurb:'Occurs on palms, soles and nail beds and is unrelated to sun exposure. It is the melanoma most often found late, particularly in brown and black skin.',
  w:{site_acral:5,look_nailstreak:5,look_flatpigment:2,col_blackblue:3,bord_uneven:2,size_large:2,chg_grew:3,fitz_56:2,fitz_34:1,dur_mid:1,dur_years_changed:2}},

 {id:'am',name:'Amelanotic melanoma',grp:'Melanoma',
  blurb:'Melanoma that makes little or no pigment, so it looks pink or skin-coloured. Routinely mistaken for a cyst, a bite or a scar until it keeps growing.',
  w:{look_pinknodule:4,col_redpink:3,col_skin:2,size_growing:3,chg_raised:2,sym_bleed:2,dur_new:2,dur_mid:2,look_fastnodule:2,risk_fam:1},
  neg:{chg_none:2,dur_years:2}},

 {id:'mcc',name:'Merkel cell carcinoma',grp:'Rare and aggressive',
  blurb:'A rare, fast, usually painless red-violet nodule of the touch-receptor cells. Strongly associated with older age and a suppressed immune system.',
  w:{look_fastnodule:4,look_pinknodule:3,site_face:3,dur_new:4,size_growing:3,col_redpink:2,risk_immuno:3,sym_none:2,bord_even:1,site_arms:1},
  neg:{dur_years:3,chg_none:2}},

 {id:'ka',name:'Keratoacanthoma',grp:'Treated as low-grade SCC',
  blurb:'A volcano-shaped lump with a central plug that erupts within weeks. It can shrink on its own, but is removed because it cannot be reliably told from SCC.',
  w:{look_fastnodule:4,look_wart:3,site_face:2,site_arms:2,dur_new:3,col_skin:2,size_growing:2,risk_outdoor:1}},

 {id:'sk',name:'Seborrhoeic keratosis',grp:'Harmless look-alike',
  blurb:'A benign warty growth that looks stuck onto the skin surface. Extremely common after middle age and often mistaken for melanoma because of its dark colour.',
  w:{look_wart:3,dur_years:4,col_uniform:2,bord_even:3,chg_none:3,site_trunk:2,size_large:1,sym_itch:1,look_darkraised:1},
  neg:{sym_bleed:1,look_sore:2,size_growing:1}},

 {id:'nevus',name:'Ordinary mole (benign naevus)',grp:'Harmless look-alike',
  blurb:'A normal mole: one colour, even outline, stable for years and resembling the person\u2019s other moles. Stability over time is the reassuring feature, not appearance alone.',
  w:{look_darkraised:3,col_uniform:4,bord_even:4,size_small:3,chg_none:4,dur_years:4,sym_none:2},
  neg:{col_multi:4,bord_uneven:3,chg_color:3,chg_grew:3,sym_bleed:3,size_growing:3}},

 {id:'df',name:'Dermatofibroma',grp:'Harmless look-alike',
  blurb:'A small firm nodule, usually on the leg, that dimples inward when pinched. Often follows an insect bite or minor injury and then stays put for years.',
  w:{site_legs:3,col_uniform:2,bord_even:2,dur_years:3,size_small:3,sym_itch:1,chg_none:2,look_darkraised:1}},

 {id:'ecz',name:'Eczema or psoriasis',grp:'Harmless look-alike',
  blurb:'Inflammatory skin disease. Typically itchy, appears in more than one place, and improves and relapses — unlike Bowen\u2019s disease, which sits in one spot and never clears.',
  w:{look_patch:3,look_scaly:3,sym_itch:3,col_redpink:2,chg_none:1,dur_years:2,site_arms:1,site_legs:1},
  neg:{sym_bleed:1,look_pearly:2,col_blackblue:2}}
];

const RED = [
  {test:a=>a.has('look_sore')&&!a.has('dur_new'),msg:'A sore that has not healed for over a month is one of the most reliable signs of a keratinocyte carcinoma.',hi:1},
  {test:a=>a.has('sym_bleed'),msg:'Bleeding without being knocked or scratched is a warning sign in any lesion, pigmented or not.',hi:1},
  {test:a=>a.has('look_nailstreak'),msg:'A dark stripe along a nail with no remembered injury needs a dermatologist to examine it, especially if it is widening.',hi:1},
  {test:a=>a.has('look_fastnodule')&&(a.has('dur_new')||a.has('size_growing')),msg:'A firm lump that has grown steadily over weeks fits the pattern of nodular melanoma and Merkel cell carcinoma — both are urgent.',hi:1},
  {test:a=>a.has('col_multi')&&a.has('bord_uneven'),msg:'Several colours together with an uneven border is the core melanoma pattern in the ABCDE rule.',hi:1},
  {test:a=>a.has('chg_color')||a.has('chg_grew')||a.has('chg_raised'),msg:'Change is the single most important warning sign. A lesion that is evolving needs assessment even if everything else looks unremarkable.',hi:0},
  {test:a=>a.has('site_acral')&&(a.has('look_flatpigment')||a.has('col_blackblue')),msg:'Pigmented lesions on palms and soles are checked carefully because acral melanoma is easy to overlook there.',hi:1},
  {test:a=>a.has('risk_immuno')&&(a.has('size_growing')||a.has('look_fastnodule')||a.has('look_wart')),msg:'A suppressed immune system raises the risk of squamous cell and Merkel cell carcinoma sharply, and makes them behave more aggressively.',hi:1},
  {test:a=>a.has('sym_crust'),msg:'A lesion that crusts, appears to heal, then reopens in the same spot is behaving like a cancer rather than a wound.',hi:1},
  {test:a=>a.has('sym_numb'),msg:'Numbness or tingling in a lesion can indicate involvement of nerves and should be mentioned to a doctor.',hi:1},
  {test:a=>a.has('dur_years_changed'),msg:'A lesion stable for years that has suddenly started to change is a recognised pattern for melanoma arising in an existing mole.',hi:1},
  {test:a=>a.has('size_large')&&a.has('bord_uneven')&&a.has('look_flatpigment'),msg:'A wide, flat, irregularly bordered pigmented patch fits superficial spreading melanoma and lentigo maligna.',hi:1}
];

function collect(){
  const s = new Set();
  document.querySelectorAll('#form input:checked').forEach(i=>s.add(i.value));
  return s;
}

function score(ans){
  return TYPES.map(t=>{
    let raw=0, hits=[];
    for(const k in t.w){ if(ans.has(k)){ raw += t.w[k]; hits.push([k,t.w[k]]); } }
    if(t.neg) for(const k in t.neg){ if(ans.has(k)) raw -= t.neg[k]; }
    hits.sort((a,b)=>b[1]-a[1]);
    return {...t, raw:Math.max(0,raw), hits:hits.slice(0,3).map(h=>h[0])};
  }).sort((a,b)=>b.raw-a.raw);
}

const LABEL = {
  site_face:'the site on the face, ear, scalp or neck', site_trunk:'the site on the trunk', site_arms:'the site on the arms or hands',
  site_legs:'the site on the leg', site_acral:'the palm, sole or nail location', site_lips:'the lip or eyelid location',
  site_covered:'the sun-protected site',
  dur_new:'how recently it appeared', dur_mid:'the few-month history', dur_long:'the long history', dur_years:'how long it has been stable',
  dur_years_changed:'a long-standing lesion that recently changed',
  look_pearly:'the pearly surface with visible vessels', look_scaly:'the rough scaly surface', look_wart:'the crusted wart-like surface',
  look_sore:'the non-healing sore', look_flatpigment:'the flat pigmented patch', look_darkraised:'the raised dark mole',
  look_fastnodule:'the fast-growing firm lump', look_pinknodule:'the unpigmented pink nodule', look_nailstreak:'the dark nail stripe',
  look_patch:'the persistent scaly plaque',
  col_uniform:'the even colour', col_multi:'the mix of colours', col_blackblue:'the black or blue-black colour',
  col_redpink:'the red or pink colour', col_skin:'the skin-coloured appearance', col_white:'the pale scar-like colour',
  bord_even:'the sharply defined edge', bord_uneven:'the uneven edge',
  size_small:'the small size', size_large:'the width over 6 mm', size_growing:'that it is getting bigger',
  chg_none:'that it has not changed', chg_grew:'that it grew wider', chg_color:'the change in colour', chg_raised:'that it became raised',
  sym_bleed:'the spontaneous bleeding', sym_crust:'the crusting and reopening', sym_itch:'the itching', sym_pain:'the tenderness',
  sym_numb:'the numbness', sym_none:'the absence of symptoms',
  risk_prev:'previous skin cancer', risk_fam:'family history of melanoma', risk_moles:'having many moles',
  risk_burns:'past sunburn or tanning bed use', risk_immuno:'immune suppression', risk_outdoor:'long-term sun exposure',
  risk_fair:'fair, easily burned skin', risk_none:'no listed risk factors',
  fitz_12:'skin that always burns', fitz_34:'skin that burns sometimes', fitz_56:'skin that rarely burns'
};

document.getElementById('run').addEventListener('click',()=>{
  const ans = collect();
  const box = document.getElementById('result');
  if(ans.size < 3){
    box.className='show';
    box.innerHTML='<div class="band b-caution"><span class="k">Not enough to work with</span><h3>Answer at least three questions</h3><p>Pick a site, how long it has been there, and what it looks like, then run it again.</p></div>';
    box.scrollIntoView({behavior:'smooth',block:'start'});
    return;
  }

  const flags = RED.filter(r=>r.test(ans));
  const hard = flags.filter(f=>f.hi===1).length;
  const ranked = score(ans);
  // a condition only qualifies if it shares at least one appearance feature with what was described
  const looks = [...ans].filter(v=>v.startsWith('look_'));
  const gated = looks.length ? ranked.filter(t=>looks.some(l=>l in t.w)) : ranked;
  const pool = gated.length ? gated : ranked;
  const top = pool[0].raw || 1;
  const shown = pool.filter(t=>t.raw >= Math.max(3, top*0.42)).slice(0,5);
  const malignantOnTop = shown.length && shown[0].grp !== 'Harmless look-alike';

  let band;
  if(hard >= 2 || (hard >= 1 && malignantOnTop)){
    band = {c:'b-urgent',k:'Suggested urgency',h:'Get this looked at within the next few days',
      p:'Your answers include more than one recognised warning sign. That does not mean it is cancer — most such lesions are not — but it does mean it should be examined soon rather than watched. Ask for an appointment with a doctor or dermatologist and say that a lesion is changing.'};
  } else if(hard === 1 || flags.length){
    band = {c:'b-caution',k:'Suggested urgency',h:'Book an appointment in the next two to four weeks',
      p:'At least one feature in your answers is one clinicians specifically look for. It is worth a proper examination rather than waiting to see what happens.'};
  } else {
    band = {c:'b-steady',k:'Suggested urgency',h:'Show it to a doctor at your next opportunity, and watch it',
      p:'Nothing you described matches the classic warning patterns. That is genuinely not the same as safe — melanoma can look completely ordinary, and this tool cannot see your skin. Photograph it next to a ruler, repeat the photo monthly, and get it checked if anything changes.'};
  }

  let html = '<div class="band '+band.c+'"><span class="k">'+band.k+'</span><h3>'+band.h+'</h3><p>'+band.p+'</p></div>';

  if(flags.length){
    html += '<h4 style="color:#fff;margin-bottom:11px">Features clinicians pay attention to in your answers</h4><ul class="flags">';
    flags.forEach(f=>{ html += '<li>'+f.msg+'</li>'; });
    html += '</ul>';
  }

  html += '<h4 style="color:#fff;margin-bottom:11px">Conditions that share the features you described</h4><div class="matches">';
  shown.forEach((t,i)=>{
    const pct = Math.round(t.raw/top*100);
    const why = t.hits.map(h=>LABEL[h]).filter(Boolean);
    html += '<div class="match'+(i===0?' top':'')+'">'
      + '<div class="match-head"><h4>'+t.name+'</h4><span class="grp">'+t.grp+'</span></div>'
      + '<div class="bar"><i style="width:'+pct+'%"></i></div>'
      + '<p>'+t.blurb+'</p>'
      + (why.length?'<p class="why">Matched on <b>'+why.join('</b>, <b>')+'</b>.</p>':'')
      + '</div>';
  });
  html += '</div>';

  html += '<div class="nextsteps"><h4>What to do next</h4><ol>'
    + '<li>Photograph the lesion in daylight with a ruler or coin beside it for scale.</li>'
    + '<li>Repeat the photograph in the same light every month so change becomes obvious.</li>'
    + '<li>Check the rest of your skin, including the soles, between the toes, the scalp and under the nails.</li>'
    + '<li>At the appointment, ask specifically for examination with a dermatoscope, and say how long it has been there and what has changed.</li>'
    + '<li>If a doctor reassures you but the lesion continues to change, go back. Persisting is reasonable.</li>'
    + '</ol></div>';

  html += '<p class="small" style="color:#7F909E;margin-top:20px">This ranking reflects only the words you selected. It has not seen your skin, cannot assess texture, pigment network or vessel pattern, and is not a diagnosis.</p>';

  box.className='show';
  box.innerHTML = html;
  box.scrollIntoView({behavior:'smooth',block:'start'});
});

document.getElementById('clear').addEventListener('click',()=>{
  document.getElementById('form').reset();
  const box=document.getElementById('result');
  box.className=''; box.innerHTML='';
});