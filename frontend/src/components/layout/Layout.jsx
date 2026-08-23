import Header from './Header'; import Sidebar from './Sidebar';
export default function Layout({tab,setTab,children}){return <><Header tab={tab} setTab={setTab}/><main><Sidebar/><section className="content">{children}</section></main></>}
