import { createContext, useContext, useState } from 'react'

const AppModeContext = createContext({ mode: 'chat', setMode: () => {} })

export function AppModeProvider({ children }) {
  const [mode, setMode] = useState('chat')
  return (
    <AppModeContext.Provider value={{ mode, setMode }}>
      {children}
    </AppModeContext.Provider>
  )
}

export const useAppMode = () => useContext(AppModeContext)
