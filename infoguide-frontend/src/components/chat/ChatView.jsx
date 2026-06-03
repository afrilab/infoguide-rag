import Header from '../layout/Header'
import SourcesSidebar from './SourcesSidebar'
import ChatPanel from './ChatPanel'

export default function ChatView() {
  return (
    <>
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <SourcesSidebar />
        <ChatPanel />
      </div>
    </>
  )
}
