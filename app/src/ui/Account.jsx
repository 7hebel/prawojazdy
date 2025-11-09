import { useEffect, useState } from 'react';
import './Account.css';


async function loadAndValidateSession() {
  const req = await fetch(import.meta.env.VITE_API + "account/validate-session/" + (localStorage.getItem("client_id") || ''));
  const resp = await req.json();
  
  if (resp.status == true) {
    localStorage.setItem("username", resp.content.username)
  }

  return resp.status
}

function AnonAccount({}) {
  // info: data saved, register to persistent
  // register form / login form

  return (
    <h1>ANON</h1>
  )
}

function UserAccount({}) {
  // show account data
  // logout btn

  return (
    <h1>{localStorage.getItem("username")} user</h1>
  )
}

export function AccountView({ closeView }) {
  const [isLogged, setIsLogged] = useState(null);

  useEffect(() => {
    loadAndValidateSession()
    .then(isLogged => {
      setIsLogged(isLogged)
    })
  })

  if (isLogged === null) {
    return (
      <div className="loader-container">
        <div className="loader"></div>
      </div>
    )
  }

  if (isLogged) {
    return <UserAccount/>
  } else {
    return <AnonAccount/>
  }
}
