(() => {
  'use strict';
  const root = document.getElementById('architecture-map');
  const stage = document.getElementById('map-stage');
  const wires = document.getElementById('map-wires');
  const dialog = document.getElementById('map-detail-dialog');
  root.querySelector('[data-map-close]').addEventListener('click',()=>dialog.close());
  const inspector = {
    status: document.getElementById('inspector-status'),
    title: document.getElementById('inspector-title'),
    description: document.getElementById('inspector-description'),
    input: document.getElementById('inspector-input'),
    output: document.getElementById('inspector-output'),
    skills: document.getElementById('inspector-skills')
  };
  const existing = 'Existing source instructions · not imported here yet';
  const imported = 'Original method preserved · generic project bindings';
  const importedSkills = new Set(['analyze-start','get-ready-to-code','deep-review','change-guard','compliance-check']);
  const prSkills = new Set(['how-to-make-a-pr','how-to-review-a-pr']);
  const nodes = {
    controller: {title:'Safe Engine keeps the whole job moving.',status:'Safe Engine 0.1.0 · local agent-operated pilot',description:'One coordinator carries the original task between skills, records progress, avoids duplicate work, and follows the session contract through the agreed local testing handoff. Work continues to the verified handoff without artificial credits or exhaustion stops; actual owner checkpoints and dependent blockers remain.',input:'A work item, discovered and reviewed project settings, available tools, delegated or reserved choices, and the agreed completion boundary.',output:'A durable run record: current stage, next owner, artifacts, and any blocker.',skills:'safe-engine · Python controller · reviewed project profile'},
    intake: {title:'Define the job.',status:existing,description:'Turn a request into a clear, deduplicated task before starting new work. UX suggestions remain in backlog until selected.',input:'The request, relevant evidence, and existing tasks or pull requests.',output:'A linked work item with an intended outcome and acceptance criteria.',skills:'how-to-write-a-clickup-task · clickup-task'},
    analysis: {title:'Understand before changing.',status:imported,description:'Read the actual code and map the callers, consumers, contracts, and user journey. Analysis is a separate phase: no code is written here.',input:'The original ask, relevant repository code, and evidence of the problem.',output:'A grounded analysis, affected areas, claim-versus-code findings, and open questions.',skills:'analyze-start'},
    build: {title:'Build from a critiqued plan.',status:imported,description:'List the files first and honor the original stop unless continuation is already authorized. Then critique the plan. For new software, research product/UX, current stack, architecture and fitting patterns, then revise the plan. Resolve material unknowns; plan CPU/GPU, memory, queries, network, storage and caching. Implement each todo through the prepare → analyze → apply → review loop. Finish the whole task and in-scope improvements, then manually exercise real behavior. Only afterward write, polish and run automated tests at the final pre-PR stage. Small fixes stay surgical; fresh review follows.',input:'The analysis, success criteria, target stack, and available check commands.',output:'Finished implementation, manual action evidence, then final automated results tied to the candidate.',skills:'get-ready-to-code · research-market for new software · Project checks'},
    pr: {title:'Package the work for review.',status:'Packaged · mandatory · project setup pending',description:'Every factory PR follows the complete creation skill: verified base, linked task, visual draft, human owner and notification. Discover project settings; unresolved bindings block PR completion while independent local build and testing continue. A draft is a review handoff, not a release.',input:'The changed code, passing applicable checks, original task and resolved project bindings.',output:'A visual draft and recorded handoff, followed by mandatory separate-instance PR review.',skills:'how-to-make-a-pr'},
    review: {title:'Challenge the work in a fresh instance.',status:'Full PR skill packaged · mandatory',description:'PR review captures the claim, analyzes real code, runs four themed reviews, then synthesizes findings and compliance. It finishes permitted surgical fixes, manually exercises them, then writes/runs final tests and prepares the handoff. Push and comment checkpoints remain. The local controller has five separate acceptance passes.',input:'The exact PR head and base, original request, decisions, project rules and current evidence.',output:'An evidence-backed PR comment; supported repairs need fresh assessment. The human receives a draft.',skills:'how-to-review-a-pr · analyze-start · get-ready-to-code · deep-review · change-guard · compliance-check'},
    security: {title:'Check security.',status:imported,description:'One deep-review pass focuses on protection: trust boundaries, access, data handling, and security regressions. Findings feed the combined reviewer verdict.',input:'The PR diff, surrounding implementation, and security review rubric.',output:'Severity-tagged security findings and a verdict.',skills:'deep-review · references/theme-security.md'},
    performance: {title:'Check real performance.',status:imported,description:'A separate pass examines the cost of the implementation for its workload: unnecessary work, repeated queries, and inefficient paths. Performance requirements depend on the problem.',input:'The change, affected call paths, and the performance rubric.',output:'Performance findings with their impact and a verdict.',skills:'deep-review · references/theme-performance.md'},
    journey: {title:'Follow the user all the way through.',status:imported,description:'Trace whether the original goal can actually be achieved, including feedback and failure paths. Look for duplicated notifications, misleading messages, and silent failures.',input:'The original request, user-facing code paths, and the user-journey rubric.',output:'Evidence of gaps in the end-to-end user outcome.',skills:'deep-review · references/theme-user-journey.md'},
    regression: {title:'Protect what already works.',status:imported,description:'Compare behavior before and after the change. Check callers, side effects, contracts, and platform compatibility where applicable.',input:'The diff, previous behavior, callers, and relevant checks.',output:'A per-file safety assessment and regression findings.',skills:'change-guard'},
    compliance: {title:'Deliver the original request.',status:imported,description:'Match the result against the original ask, accepted plan, and project rules. Sound code can still fail if it solves the wrong problem.',input:'The original requirements, agreed plan, project rules, and changed code.',output:'Requirement traceability: met, partial, missing, or uncertain; plus a verdict.',skills:'compliance-check'},
    approval: {title:'You make the release decision.',status:'Human boundary · source leaves the PR as draft',description:'Review the checked change and unresolved flags. Request fixes, stop the work, or authorize the applicable release path. A reviewer verdict alone does not ship software.',input:'The draft PR, original criteria, check evidence, reviewer verdict, and blockers.',output:'A human decision: approve the next step, request changes, or stop.',skills:'Human owner · how-to-make-a-pr and how-to-review-a-pr preserve this boundary'},
    release: {title:'Ship, then check the live result.',status:'Proposed capability · to be built',description:'Release the approved revision through the target project’s process. Check that it works after deployment and follow the recovery plan if it fails.',input:'The approved revision, release authorization, deployment access, and recovery plan.',output:'Deployment evidence and smoke-check results, or a recovery report and blocker.',skills:'Proposed: release-change'},
    observe: {title:'Turn real outcomes into better work.',status:'Partial source coverage · general monitoring loop to be built',description:'Investigate evidenced defects and user friction. A bug can produce a deduplicated fix task; a UX improvement is a backlog proposal. General release monitoring still needs connecting.',input:'Agreed health signals, incident evidence, or a relevant user session.',output:'An evidenced defect task or a UX backlog proposal, without duplicating existing work.',skills:'bug-investigation · ux-investigation · Proposed: observe-release'}
  };
  const groups = [
    {name:'Delivery core',description:'The playbooks that take a software task from request to reviewed change.',skills:['analyze-start','get-ready-to-code','deep-review','change-guard','compliance-check','how-to-make-a-pr','how-to-review-a-pr','how-to-write-a-clickup-task','clickup-task']},
    {name:'Investigation & specialists',description:'Bring evidence into the pipeline, improve handoffs, and support relevant content work.',skills:['bug-investigation','ux-investigation','communication-style-in-development','seo-content-redaktion']},
    {name:'System adapters',description:'Reference playbooks for working with the relevant services. Actual tool access still needs provisioning.',skills:['superchat-api','repaircheck-api','autoixpert-api','autoixpert-computer-use','dat-api','notion-api']},
    {name:'Business workflows',description:'Domain work the factory can build and maintain. These are not mandatory steps on every code task.',skills:['anwalt-versand-abgleich','auftragsboerse-monitor','autoixpert-gutachten-aufgaben-abgleich','autoixpert-payment-reminders','dat-kalkulation-v2','dat-kalkulation-v3','dat-sv-abgleich','dispatch-appraiser','dokument-generisch','dokument-unfallbericht','dokument-versicherungsschreiben','gutachten-aufbereitung','legal-check','marktwertanalyse','post-submission-eval','pre-appraisal','repaircheck-briefpapier','repairshop-outreach','superchat-reply']}
  ];
  const skillRoutes = {'analyze-start':'analysis','get-ready-to-code':'build','change-guard':'regression','compliance-check':'compliance','how-to-make-a-pr':'pr','how-to-review-a-pr':'review','how-to-write-a-clickup-task':'intake','clickup-task':'intake','bug-investigation':'observe','ux-investigation':'observe'};
  const specialistDetails = {
    'deep-review':'Mobile original code-quality review. The PR workflow supplies separate generic rubrics; local acceptance uses its own five-pass orchestration.',
    'communication-style-in-development':'A playbook for clear technical messages and visual explanations across the delivery workflow.',
    'seo-content-redaktion':'An editorial workflow for relevant SEO pages and articles, including its own checking helper.',
    'superchat-api':'Reference procedures for customer-conversation exports, notes, labels, assignments, and messages.',
    'repaircheck-api':'Reference procedures for RepairCheck case lookups, attachments, and backend fields.',
    'autoixpert-api':'Reference procedures for reading and writing appraisal records through the autoiXpert API.',
    'autoixpert-computer-use':'Reference procedures for tasks that need the autoiXpert browser interface.',
    'dat-api':'Reference procedures for the DAT services used by the domain workflows.',
    'notion-api':'Reference procedures for database schemas and recording workflow results in Notion.',
    'anwalt-versand-abgleich':'Finds completed appraisals with a lawyer recorded but no recorded email dispatch to the law firm.',
    'auftragsboerse-monitor':'Classifies incoming job offers and requests, records them, and follows the source’s defined offer workflow.',
    'autoixpert-gutachten-aufgaben-abgleich':'Finds open appraisal reports without a matching open task.',
    'autoixpert-payment-reminders':'A domain runbook for payment reminders, escalation stages, and invoice-note checks.',
    'dat-kalkulation-v2':'A gated runbook for repair calculations from vehicle identity and damage information.',
    'dat-kalkulation-v3':'A broader case-to-calculation workflow, including appraisal preparation and system handoffs.',
    'dat-sv-abgleich':'Compares the initial repair calculation with the appraiser’s later calculation.',
    'dispatch-appraiser':'A domain procedure for selecting and inviting suitable appraisers for a case.',
    'dokument-generisch':'Processes customer documents that do not fit a specific document category, extracting supported case facts.',
    'dokument-unfallbericht':'Extracts supported accident and party information from an accident report.',
    'dokument-versicherungsschreiben':'Extracts case information from insurer correspondence and flags special situations.',
    'gutachten-aufbereitung':'Prepares an appraisal case from its photos, documents, and supported vehicle and accident information.',
    'legal-check':'A domain playbook for an initial assessment of relevant insurance fee reductions or recovery requests.',
    'marktwertanalyse':'Researches vehicle-market listings and produces a source-backed market analysis.',
    'post-submission-eval':'Evaluates a submitted case against the source’s gates for a repair-recommendation workflow.',
    'pre-appraisal':'Prepares and checks an appraisal record before the appraisal itself.',
    'repaircheck-briefpapier':'Produces branded document artifacts in RepairCheck’s letterhead format.',
    'repairshop-outreach':'A bounded partner-workshop outreach procedure linked to a qualifying case.',
    'superchat-reply':'Drafts a suggested customer reply as an internal note for human review.'
  };
  let selected = 'intake';
  let activeView = 'delivery';
  const reviewKeys = new Set(['review','security','performance','journey','regression','compliance']);

  function inspect(key, skill, group) {
    selected = key;
    let detail = nodes[key];
    if (!detail) {
      detail = {title:skill,status:existing,description:specialistDetails[skill] || group.description,input:group.name==='System adapters'?'A service-specific task and provisioned tool access.':'The context and evidence required by this skill’s entrypoint.',output:group.name==='System adapters'?'The service procedures and constraints needed by the calling workflow.':group.name==='Business workflows'?'The outcome specified by the source playbook. Domain routines have not all undergone a full operational audit.':'An assessment or artifact following this source playbook. It supports the delivery workflow when relevant.',skills:skill};
    }
    if (skill && skillRoutes[skill]) detail = {...detail,skills:skill};
    if (!skill && key==='regression') detail = {...detail,skills:'how-to-review-a-pr / references/theme-change-guard.md'};
    if (!skill && key==='compliance') detail = {...detail,title:'Synthesize without changing the author’s intent.',description:'Merge and deduplicate the four themed reports. Preserve necessary complexity, note opportunities, and check that proposed fixes respect the original request. Keep current findings separate from hypothetical fixes.',input:'The four themed reports, original PR claim, analysis, and authorized scope.',output:'A current-candidate verdict, permitted fix-set, flagged opportunities, and open questions.',skills:'how-to-review-a-pr / references/synthesis-and-verdict.md'};
    if (skill) detail = {...detail,status:prSkills.has(skill)?nodes[key].status:importedSkills.has(skill)?imported:existing};
    if (skill==='how-to-review-a-pr') detail = {...detail,description:'The complete PR-review skill is packaged and mandatory for every factory PR, on a separate instance. It follows four themed reviews, synthesis/compliance, permitted corrections, push/comment checkpoints and detailed handoff. Missing execution or project settings block completion.'};
    Object.keys(inspector).forEach(field=>inspector[field].textContent=detail[field]);
    root.querySelectorAll('[data-map-node]').forEach(button=>{
      const active=button.dataset.mapNode===key && activeView==='delivery';
      button.classList.toggle('is-active',active);
      button.setAttribute('aria-pressed',String(active));
    });
    root.querySelectorAll('[data-library-skill]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.librarySkill===skill)));
    highlightWires();
  }

  function highlightWires(){
    const related=reviewKeys.has(selected)?'review':selected;
    wires.querySelectorAll('path[data-from]').forEach(path=>path.classList.toggle('active',path.dataset.from===related||path.dataset.to===related));
  }

  root.querySelectorAll('[data-map-node]').forEach(button=>button.addEventListener('click',()=>{inspect(button.dataset.mapNode);dialog.showModal();}));
  const library=document.getElementById('map-library');
  groups.forEach(group=>{
    const section=document.createElement('section');section.className='library-group';
    const header=document.createElement('div');header.className='library-head';
    const title=document.createElement('strong');title.textContent=group.name;
    const count=document.createElement('span');count.textContent=String(group.skills.length)+' skills';
    header.append(title,count);
    const description=document.createElement('p');description.textContent=group.description;
    const list=document.createElement('div');list.className='library-skills';
    group.skills.forEach(skill=>{
      const button=document.createElement('button');button.type='button';button.className='library-skill';button.textContent=skill;button.dataset.librarySkill=skill;button.setAttribute('aria-pressed','false');button.setAttribute('aria-controls','map-inspector');
      button.addEventListener('click',()=>{inspect(skillRoutes[skill]||skill,skill,group);dialog.showModal();});list.append(button);
    });
    section.append(header,description,list);library.append(section);
  });

  const tabs=[document.getElementById('delivery-tab'),document.getElementById('library-tab')];
  function switchView(tab){
    tabs.forEach(item=>{const active=item===tab;item.setAttribute('aria-selected',String(active));item.tabIndex=active?0:-1;document.getElementById(item.getAttribute('aria-controls')).hidden=!active;});
    activeView=tab===tabs[0]?'delivery':'library';
    if(activeView==='delivery'){inspect('intake');requestAnimationFrame(drawWires);}else{inspect('analysis','analyze-start',groups[0]);}
  }
  tabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>switchView(tab));
    tab.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight'||event.key==='ArrowLeft')next=tabs[1-index];if(event.key==='Home')next=tabs[0];if(event.key==='End')next=tabs[1];if(next){event.preventDefault();switchView(next);next.focus();}});
  });

  const svgNS='http://www.w3.org/2000/svg';
  function drawWires(){
    if(document.getElementById('delivery-panel').hidden)return;
    const base=stage.getBoundingClientRect();
    if(!base.width||!base.height)return;
    wires.setAttribute('viewBox',`0 0 ${base.width} ${base.height}`);
    wires.replaceChildren();
    const defs=document.createElementNS(svgNS,'defs');
    [['normal','#899780'],['feedback','#ac5c3f'],['proposed','#9a8f80']].forEach(([id,color])=>{
      const marker=document.createElementNS(svgNS,'marker');marker.id='factory-arrow-'+id;marker.setAttribute('viewBox','0 0 8 8');marker.setAttribute('refX','7');marker.setAttribute('refY','4');marker.setAttribute('markerWidth','6');marker.setAttribute('markerHeight','6');marker.setAttribute('orient','auto');
      const head=document.createElementNS(svgNS,'path');head.setAttribute('d','M1 1 7 4 1 7');head.setAttribute('fill','none');head.setAttribute('stroke',color);head.setAttribute('stroke-width','1.3');marker.append(head);defs.append(marker);
    });wires.append(defs);
    const rects={};
    stage.querySelectorAll('[data-wire-node]').forEach(element=>{const r=element.getBoundingClientRect();rects[element.dataset.wireNode]={l:r.left-base.left,r:r.right-base.left,t:r.top-base.top,b:r.bottom-base.top,cx:r.left-base.left+r.width/2,cy:r.top-base.top+r.height/2};});
    function edge(from,to,d,type='normal'){
      const path=document.createElementNS(svgNS,'path');path.setAttribute('d',d);path.setAttribute('class','map-wire '+(type==='normal'?'':type));path.setAttribute('marker-end','url(#factory-arrow-'+(type==='artifact'?'normal':type)+')');path.dataset.from=from;path.dataset.to=to;wires.append(path);
    }
    const {controller,intake,analysis,build,pr,review,approval,release,observe}=rects;
    const mobile=window.matchMedia('(max-width:680px)').matches;
    function vertical(from,to,type='normal'){const a=rects[from],b=rects[to];const y=(a.b+b.t)/2;edge(from,to,`M${a.cx},${a.b+2} V${y} H${b.cx} V${b.t-3}`,type);}
    if(mobile){
      [['controller','intake','proposed'],['intake','analysis'],['analysis','build'],['build','pr'],['pr','review'],['review','approval'],['approval','release','proposed'],['release','observe','proposed']].forEach(args=>vertical(...args));
    }else{
      edge('controller','intake',`M${intake.cx},${controller.b+2} V${intake.t-3}`,'proposed');
      edge('controller','build',`M${build.cx},${controller.b+2} V${build.t-3}`,'proposed');
      [['intake','analysis'],['analysis','build'],['build','pr']].forEach(([from,to])=>{const a=rects[from],b=rects[to];edge(from,to,`M${a.r+2},${a.cy} H${b.l-3}`);});
      const routeY=pr.b+21;
      edge('pr','review',`M${pr.cx},${pr.b+2} V${routeY} H${review.cx} V${review.t-3}`);
      edge('review','approval',`M${review.r+2},${approval.cy} H${approval.l-3}`);
      edge('review','build',`M${review.r-35},${review.t-2} V${pr.b+43} H${build.cx} V${build.b+3}`,'feedback');
      const lowerRouteY=review.b+(release.t-review.b)/2;
      edge('approval','release',`M${approval.cx},${approval.b+2} V${lowerRouteY} H${release.cx} V${release.t-3}`,'proposed');
      edge('release','observe',`M${release.r+2},${release.cy} H${observe.l-3}`,'proposed');
      edge('observe','intake',`M${observe.cx},${observe.b+2} V${observe.b+14} H10 V${intake.cy} H${intake.l-3}`,'feedback');
    }
    highlightWires();
  }
  let resizeFrame;
  new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(drawWires);}).observe(stage);
  inspect('intake');
  requestAnimationFrame(drawWires);
})();
