function t(t,e,s,i){var r,n=arguments.length,o=n<3?e:null===i?i=Object.getOwnPropertyDescriptor(e,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(t,e,s,i);else for(var a=t.length-1;a>=0;a--)(r=t[a])&&(o=(n<3?r(o):n>3?r(e,s,o):r(e,s))||o);return n>3&&o&&Object.defineProperty(e,s,o),o}"function"==typeof SuppressedError&&SuppressedError;
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const e=globalThis,s=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),r=new WeakMap;let n=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(s&&void 0===t){const s=void 0!==e&&1===e.length;s&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&r.set(e,t))}return t}toString(){return this.cssText}};const o=(t,...e)=>{const s=1===t.length?t[0]:e.reduce((e,s,i)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[i+1],t[0]);return new n(s,t,i)},a=s?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return(t=>new n("string"==typeof t?t:t+"",void 0,i))(e)})(t):t,{is:l,defineProperty:h,getOwnPropertyDescriptor:c,getOwnPropertyNames:d,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,_=globalThis,g=_.trustedTypes,f=g?g.emptyScript:"",m=_.reactiveElementPolyfillSupport,$=(t,e)=>t,y={toAttribute(t,e){switch(e){case Boolean:t=t?f:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let s=t;switch(e){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t)}catch(t){s=null}}return s}},v=(t,e)=>!l(t,e),A={attribute:!0,type:String,converter:y,reflect:!1,useDefault:!1,hasChanged:v};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */Symbol.metadata??=Symbol("metadata"),_.litPropertyMetadata??=new WeakMap;let b=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=A){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(t,s,e);void 0!==i&&h(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){const{get:i,set:r}=c(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:i,set(e){const n=i?.call(this);r?.call(this,e),this.requestUpdate(t,n,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??A}static _$Ei(){if(this.hasOwnProperty($("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty($("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty($("properties"))){const t=this.properties,e=[...d(t),...p(t)];for(const s of e)this.createProperty(s,t[s])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const s=this._$Eu(t,e);void 0!==s&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const s=new Set(t.flat(1/0).reverse());for(const t of s)e.unshift(a(t))}else void 0!==t&&e.push(a(t));return e}static _$Eu(t,e){const s=e.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,i)=>{if(s)t.adoptedStyleSheets=i.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const s of i){const i=document.createElement("style"),r=e.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=s.cssText,t.appendChild(i)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){const s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(void 0!==i&&!0===s.reflect){const r=(void 0!==s.converter?.toAttribute?s.converter:y).toAttribute(e,s.type);this._$Em=t,null==r?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){const s=this.constructor,i=s._$Eh.get(t);if(void 0!==i&&this._$Em!==i){const t=s.getPropertyOptions(i),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:y;this._$Em=i;const n=r.fromAttribute(e,t.type);this[i]=n??this._$Ej?.get(i)??n,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(void 0!==t){const n=this.constructor;if(!1===i&&(r=this[t]),s??=n.getPropertyOptions(t),!((s.hasChanged??v)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,s))))return;this.C(t,e,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},n){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??e??this[t]),!0!==r||void 0!==n)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),!0===i&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,s]of t){const{wrapped:t}=s,i=this[e];!0!==t||this._$AL.has(e)||void 0===i||this.C(e,void 0,s,i)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[$("elementProperties")]=new Map,b[$("finalized")]=new Map,m?.({ReactiveElement:b}),(_.reactiveElementVersions??=[]).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const x=globalThis,S=t=>t,E=x.trustedTypes,w=E?E.createPolicy("lit-html",{createHTML:t=>t}):void 0,C="$lit$",P=`lit$${Math.random().toFixed(9).slice(2)}$`,k="?"+P,T=`<${k}>`,U=document,M=()=>U.createComment(""),O=t=>null===t||"object"!=typeof t&&"function"!=typeof t,H=Array.isArray,N="[ \t\n\f\r]",R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,L=/-->/g,j=/>/g,I=RegExp(`>|${N}(?:([^\\s"'>=/]+)(${N}*=${N}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),D=/'/g,z=/"/g,B=/^(?:script|style|textarea|title)$/i,V=(t=>(e,...s)=>({_$litType$:t,strings:e,values:s}))(1),W=Symbol.for("lit-noChange"),X=Symbol.for("lit-nothing"),q=new WeakMap,G=U.createTreeWalker(U,129);function F(t,e){if(!H(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==w?w.createHTML(e):e}const K=(t,e)=>{const s=t.length-1,i=[];let r,n=2===e?"<svg>":3===e?"<math>":"",o=R;for(let e=0;e<s;e++){const s=t[e];let a,l,h=-1,c=0;for(;c<s.length&&(o.lastIndex=c,l=o.exec(s),null!==l);)c=o.lastIndex,o===R?"!--"===l[1]?o=L:void 0!==l[1]?o=j:void 0!==l[2]?(B.test(l[2])&&(r=RegExp("</"+l[2],"g")),o=I):void 0!==l[3]&&(o=I):o===I?">"===l[0]?(o=r??R,h=-1):void 0===l[1]?h=-2:(h=o.lastIndex-l[2].length,a=l[1],o=void 0===l[3]?I:'"'===l[3]?z:D):o===z||o===D?o=I:o===L||o===j?o=R:(o=I,r=void 0);const d=o===I&&t[e+1].startsWith("/>")?" ":"";n+=o===R?s+T:h>=0?(i.push(a),s.slice(0,h)+C+s.slice(h)+P+d):s+P+(-2===h?e:d)}return[F(t,n+(t[s]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),i]};class J{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,n=0;const o=t.length-1,a=this.parts,[l,h]=K(t,e);if(this.el=J.createElement(l,s),G.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(i=G.nextNode())&&a.length<o;){if(1===i.nodeType){if(i.hasAttributes())for(const t of i.getAttributeNames())if(t.endsWith(C)){const e=h[n++],s=i.getAttribute(t).split(P),o=/([.?@])?(.*)/.exec(e);a.push({type:1,index:r,name:o[2],strings:s,ctor:"."===o[1]?et:"?"===o[1]?st:"@"===o[1]?it:tt}),i.removeAttribute(t)}else t.startsWith(P)&&(a.push({type:6,index:r}),i.removeAttribute(t));if(B.test(i.tagName)){const t=i.textContent.split(P),e=t.length-1;if(e>0){i.textContent=E?E.emptyScript:"";for(let s=0;s<e;s++)i.append(t[s],M()),G.nextNode(),a.push({type:2,index:++r});i.append(t[e],M())}}}else if(8===i.nodeType)if(i.data===k)a.push({type:2,index:r});else{let t=-1;for(;-1!==(t=i.data.indexOf(P,t+1));)a.push({type:7,index:r}),t+=P.length-1}r++}}static createElement(t,e){const s=U.createElement("template");return s.innerHTML=t,s}}function Z(t,e,s=t,i){if(e===W)return e;let r=void 0!==i?s._$Co?.[i]:s._$Cl;const n=O(e)?void 0:e._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),void 0===n?r=void 0:(r=new n(t),r._$AT(t,s,i)),void 0!==i?(s._$Co??=[])[i]=r:s._$Cl=r),void 0!==r&&(e=Z(t,r._$AS(t,e.values),r,i)),e}class Q{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??U).importNode(e,!0);G.currentNode=i;let r=G.nextNode(),n=0,o=0,a=s[0];for(;void 0!==a;){if(n===a.index){let e;2===a.type?e=new Y(r,r.nextSibling,this,t):1===a.type?e=new a.ctor(r,a.name,a.strings,this,t):6===a.type&&(e=new rt(r,this,t)),this._$AV.push(e),a=s[++o]}n!==a?.index&&(r=G.nextNode(),n++)}return G.currentNode=U,i}p(t){let e=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}}class Y{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=X,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Z(this,t,e),O(t)?t===X||null==t||""===t?(this._$AH!==X&&this._$AR(),this._$AH=X):t!==this._$AH&&t!==W&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>H(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==X&&O(this._$AH)?this._$AA.nextSibling.data=t:this.T(U.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:s}=t,i="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=J.createElement(F(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{const t=new Q(i,this),s=t.u(this.options);t.p(e),this.T(s),this._$AH=t}}_$AC(t){let e=q.get(t.strings);return void 0===e&&q.set(t.strings,e=new J(t)),e}k(t){H(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let s,i=0;for(const r of t)i===e.length?e.push(s=new Y(this.O(M()),this.O(M()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=S(t).nextSibling;S(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class tt{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=X,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=X}_$AI(t,e=this,s,i){const r=this.strings;let n=!1;if(void 0===r)t=Z(this,t,e,0),n=!O(t)||t!==this._$AH&&t!==W,n&&(this._$AH=t);else{const i=t;let o,a;for(t=r[0],o=0;o<r.length-1;o++)a=Z(this,i[s+o],e,o),a===W&&(a=this._$AH[o]),n||=!O(a)||a!==this._$AH[o],a===X?t=X:t!==X&&(t+=(a??"")+r[o+1]),this._$AH[o]=a}n&&!i&&this.j(t)}j(t){t===X?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class et extends tt{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===X?void 0:t}}class st extends tt{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==X)}}class it extends tt{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=Z(this,t,e,0)??X)===W)return;const s=this._$AH,i=t===X&&s!==X||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==X&&(s===X||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class rt{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){Z(this,t)}}const nt=x.litHtmlPolyfillSupport;nt?.(J,Y),(x.litHtmlVersions??=[]).push("3.3.3");const ot=globalThis;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */class at extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,s)=>{const i=s?.renderBefore??e;let r=i._$litPart$;if(void 0===r){const t=s?.renderBefore??null;i._$litPart$=r=new Y(e.insertBefore(M(),t),t,void 0,s??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return W}}at._$litElement$=!0,at.finalized=!0,ot.litElementHydrateSupport?.({LitElement:at});const lt=ot.litElementPolyfillSupport;lt?.({LitElement:at}),(ot.litElementVersions??=[]).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ht={attribute:!0,type:String,converter:y,reflect:!1,hasChanged:v},ct=(t=ht,e,s)=>{const{kind:i,metadata:r}=s;let n=globalThis.litPropertyMetadata.get(r);if(void 0===n&&globalThis.litPropertyMetadata.set(r,n=new Map),"setter"===i&&((t=Object.create(t)).wrapped=!0),n.set(s.name,t),"accessor"===i){const{name:i}=s;return{set(s){const r=e.get.call(this);e.set.call(this,s),this.requestUpdate(i,r,t,!0,s)},init(e){return void 0!==e&&this.C(i,void 0,t,e),e}}}if("setter"===i){const{name:i}=s;return function(s){const r=this[i];e.call(this,s),this.requestUpdate(i,r,t,!0,s)}}throw Error("Unsupported decorator location: "+i)};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function dt(t){return function(t){return(e,s)=>"object"==typeof s?ct(t,e,s):((t,e,s)=>{const i=e.hasOwnProperty(s);return e.constructor.createProperty(s,t),i?Object.getOwnPropertyDescriptor(e,s):void 0})(t,e,s)}({...t,state:!0,attribute:!1})}function pt(t,e,s){return t.subscribeMessage(t=>e(t),{type:"render_template",template:s.template,entity_ids:s.entity_ids,variables:s.variables,timeout:s.timeout,strict:s.strict})}function ut(t){return!!t&&(t.includes("{{")||t.includes("{%")||t.includes("{%-"))}const _t={en:{mood_happy:"Happy",mood_sad:"Sad",mood_hungry:"Hungry",mood_thirsty:"Thirsty",mood_sleepy:"Sleepy",mood_angry:"Angry",mood_playful:"Playful",level:"Level",xp:"XP",health:"Health",hunger:"Hunger",energy:"Energy",happiness:"Happiness",tree_level:"Tree",xp_to_next:"XP to next level",click_to_gain:"Click to gain XP"},de:{mood_happy:"Glücklich",mood_sad:"Traurig",mood_hungry:"Hungrig",mood_thirsty:"Durstig",mood_sleepy:"Müde",mood_angry:"Wütend",mood_playful:"Verspielt",level:"Level",xp:"XP",health:"Gesundheit",hunger:"Hunger",energy:"Energie",happiness:"Glücklichkeit",tree_level:"Baum",xp_to_next:"XP bis zum nächsten Level",click_to_gain:"Klicke um XP zu erhalten"}};!function(t){const e=window;e.customCards=e.customCards||[],e.customCards.push({...t,preview:!0})}({type:"little-buddy-card",name:"Little Buddy Card",description:"A gamified Lovelace card (little buddy card, lbc) with growable pixel-art pets and trees.",documentationURL:"https://github.com/icem0/little-buddy-card/blob/main/README.md"});let gt=class extends at{_config;_hass;_templateResults={};_unsubTemplates=new Map;static get properties(){return{_config:{state:!0},_hass:{state:!0},_templateResults:{state:!0}}}static async getConfigElement(){return document.createElement("little-buddy-card-editor")}static getStubConfig(){return{name:"Little Buddy",mood:"input_select.little_buddy_mood",xp:"input_number.little_buddy_xp",level:"input_number.little_buddy_level",health:"input_number.little_buddy_health",hunger:"input_number.little_buddy_hunger",energy:"input_number.little_buddy_energy",happiness:"input_number.little_buddy_happiness",tree_level:"input_select.little_buddy_tree_level",xp_per_click:"input_number.little_buddy_xp_per_click"}}setConfig(t){if(!t)throw new Error("Invalid configuration");this._config=t}set hass(t){this._hass=t}connectedCallback(){super.connectedCallback(),this._tryConnectTemplates()}disconnectedCallback(){super.disconnectedCallback(),this._tryDisconnectTemplates()}_tryConnectTemplates(){if(!this._hass||!this._config)return;const t={name:this._config.name};for(const[e,s]of Object.entries(t))if(!this._unsubTemplates.has(e)&&s&&ut(s))try{const t=pt(this._hass.connection,t=>{this._templateResults={...this._templateResults,[e]:t.result}},{template:s,entity_ids:this._config?.mood,variables:{config:this._config,user:this._hass.user?.name},strict:!0});this._unsubTemplates.set(e,t)}catch{}}_tryDisconnectTemplates(){this._unsubTemplates.forEach(t=>{t.then(t=>t()).catch(()=>{})}),this._unsubTemplates.clear()}_resolveValue(t,e){return t?ut(t)?this._templateResults[e]??t:t:""}getState(t){if(t&&this._hass?.states?.[t])return this._hass.states[t].state}getStateNum(t){const e=this.getState(t);return null!=e?parseFloat(e):0}getStateStr(t){const e=this.getState(t);return null!=e?String(e):""}resolveMood(){const t=this._config?.moods;if(Array.isArray(t)&&t.length)for(const e of t)if(e?.entity&&void 0!==e?.state&&e?.mood&&this.getStateStr(e.entity)===String(e.state))return e.mood;return this.getStateStr(this._config?.mood)||"happy"}getXpPerClick(){const t=this._config?.xp_per_click;if(t){const e=this.getStateNum(t);if(!isNaN(e)&&e>0)return Math.floor(e)}return 10}getPetImageUrl(){const t=this._config?.gif_url;if(t){const e=this.getStateStr(t);if(e)return e}const e=this.assetExt(),s=this.resolveMood(),i=this.getStateNum(this._config?.level)||1;return`/local/little-buddy-card/pets/level_${Math.min(Math.max(i,1),5)}/${s}.${e}`}getTreeImageUrl(){const t=this._config?.tree_gif_url;if(t){const e=this.getStateStr(t);if(e)return e}const e=this.assetExt();return`/local/little-buddy-card/trees/${this.getStateStr(this._config?.tree_level)||"seed"}.${e}`}assetExt(){const t=this._config?.asset_ext;return"gif"===t||"png"===t?t:"png"}async _handlePetClick(t){const e=this._config?.tap_action;if(e&&e.action&&"none"!==e.action)return void this._runAction(e);if(!this._hass||!this._config?.xp)return;const s=this._config.xp,i=this.getStateNum(s)+this.getXpPerClick();try{await this._hass.callService("input_number","set_value",{entity_id:s,value:i})}catch(t){console.error("Failed to set XP:",t)}}_runAction(t){if(!this._hass)return;const e=this._hass;switch(t.action){case"more-info":t.entity&&e.callService("homeassistant","more-info",{entity_id:t.entity});break;case"toggle":t.entity&&e.callService("homeassistant","toggle",{entity_id:t.entity});break;case"navigate":t.navigation_path&&window.history.pushState(null,"",t.navigation_path);break;case"url":t.url_path&&window.open(t.url_path,"_blank");break;case"call-service":case"perform-action":if(t.service){const[s,i]=t.service.split(".");try{e.callService(s,i,t.data??{})}catch(t){console.error("Action failed:",t)}}}}render(){if(!this._hass||!this._config)return V``;const t=(e=this._hass,e?.locale?.language?e.locale.language:(navigator.language||navigator.languages?.[0]||"en").startsWith("de")?"de":"en");var e;const s=_t[t]||_t.en,i=this.resolveMood(),r=s[`mood_${i}`]||i,n=this.getStateNum(this._config?.xp)||0,o=Math.floor(n/1e3)+1,a=Math.min(o,5),l=this.getStateNum(this._config?.health)||0,h=this.getStateNum(this._config?.hunger)||0,c=this.getStateNum(this._config?.energy)||0,d=this.getStateNum(this._config?.happiness)||0,p=this._resolveValue(this._config?.name||this._config?.title,"name")||"Little Buddy";return V`
      <div class="card" @click=${this._handlePetClick}>
        <div class="header">
          <div class="title">${p}</div>
          <div class="xp">${s.level}: ${a} · XP: ${n}</div>
        </div>
        <div class="content">
          <div class="pet-wrapper">
            <img class="pet" src="${this.getPetImageUrl()}" alt="Little Buddy" @error=${this._onImgError} />
          </div>
          <img class="tree" src="${this.getTreeImageUrl()}" alt="Buddy Tree" @error=${this._onImgError} />
        </div>
        <div class="stats">
          <div class="stat">
            <span class="label">${s.health}:</span> <span class="value">${l}</span>
          </div>
          <div class="stat">
            <span class="label">${s.hunger}:</span> <span class="value">${h}</span>
          </div>
          <div class="stat">
            <span class="label">${s.energy}:</span> <span class="value">${c}</span>
          </div>
          <div class="stat">
            <span class="label">${s.happiness}:</span> <span class="value">${d}</span>
          </div>
        </div>
        <div class="xp-bar">
          <div class="xp-bar-bg"></div>
          <div class="xp-bar-fill" style="width: ${n%1e3/10}%"></div>
          <div class="xp-text">${n%1e3} / 1000 ${s.xp_to_next}</div>
        </div>
        <div class="mood">
          <span class="label">${s.mood_happy}:</span> <span class="value">${r}</span>
          <span class="hint">${s.click_to_gain}</span>
        </div>
      </div>
    `}_onImgError(t){const e=t.target;e.src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",e.alt="Image not found"}static get styles(){return o`
      .card {
        --lbc-spacing: var(--mush-spacing, 12px);
        padding: var(--lbc-spacing);
        background-color: var(--card-background-color, var(--background-color));
        border-radius: var(--ha-card-border-radius, var(--border-radius, 12px));
        box-shadow: var(--ha-card-box-shadow, none);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--lbc-spacing);
        cursor: pointer;
        color: var(--primary-text-color, var(--text-color));
        transition: box-shadow 0.2s ease;
      }
      .card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
      .header {
        display: flex;
        justify-content: space-between;
        width: 100%;
        font-size: 1.1em;
        color: var(--primary-text-color, var(--text-color));
      }
      .content {
        display: flex;
        gap: 24px;
        align-items: flex-end;
      }
      .pet-wrapper {
        width: 128px;
        height: 128px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
      }
      .pet {
        height: 128px;
        width: auto;
        image-rendering: pixelated;
        pointer-events: none;
      }
      .tree {
        height: 128px;
        width: auto;
        image-rendering: pixelated;
      }
      .stats {
        display: grid;
        gap: 6px;
        width: 100%;
        font-size: 0.9em;
        color: var(--secondary-text-color, var(--text-color));
      }
      .stat {
        display: flex;
        justify-content: space-between;
      }
      .label {
        font-weight: 500;
        color: var(--secondary-text-color, var(--text-color));
      }
      .xp-bar {
        width: 100%;
        background: var(--divider-color, var(--grey-light-2));
        border-radius: 4px;
        overflow: hidden;
        height: 8px;
        position: relative;
      }
      .xp-bar-bg {
        width: 100%;
        height: 100%;
        background: var(--divider-color, var(--grey-light-2));
      }
      .xp-bar-fill {
        height: 100%;
        background: var(--accent-color, var(--paper-item-selected-color));
        width: 0%;
        transition: width 0.2s ease;
      }
      .xp-text {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        text-align: center;
        line-height: 8px;
        font-size: 0.75em;
        color: var(--primary-text-color, var(--text-color));
        pointer-events: none;
      }
      .mood {
        margin-top: 8px;
        font-size: 0.9em;
        text-align: center;
        width: 100%;
        color: var(--secondary-text-color, var(--text-color));
      }
      .hint {
        font-size: 0.75em;
        opacity: 0.7;
        margin-top: 4px;
      }
    `}};t([dt()],gt.prototype,"_config",void 0),t([dt()],gt.prototype,"_hass",void 0),t([dt()],gt.prototype,"_templateResults",void 0),gt=t([(t=>(e,s)=>{void 0!==s?s.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)})("little-buddy-card")],gt);export{gt as LittleBuddyCard};
