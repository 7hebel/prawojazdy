import { useEffect, useState, useRef } from 'react';
import './Account.css';
import { InputGroup, InputLabel, Input, FormPrimaryButton, FormSecondaryButton } from './Ui';
import { ArrowRight, DoorOpen, LockKeyholeIcon, User } from 'lucide-react';


async function loadAndValidateSession() {
  if (!localStorage.getItem("client_id")) {
    return false;
  }
  
  const req = await fetch(import.meta.env.VITE_API + "account/validate-session/" + (localStorage.getItem("client_id") || ''));
  const resp = await req.json();
  
  if (resp.status == true) {
    localStorage.setItem("username", resp.content.username)
  }

  return resp.status
}


function IdentificationProcess({ close }) {
  const [username, setUsername] = useState(null);
  const [isLogin, setIsLogin] = useState(null);

  const passwordEl = useRef(null);
  const passwordRepeatEl = useRef(null);

  if (username === null) {
    function handleUsername() {
      const input_username = document.getElementById("account-username").value;
      if (input_username.length < 3 || input_username.length > 32) return;

      (async () => {
        const req = await fetch(import.meta.env.VITE_API + "account/check-username/" + input_username);
        const resp = await req.json();
        setUsername(input_username);
        setIsLogin(resp.status)
      })();
    }

    return (
      <div className='identification-step'>
        <InputGroup>
          <InputLabel><User />Nazwa użytkownika</InputLabel>
          <Input id='account-username' placeholder={'nazwa_użytkownika'} minlen={5} maxlen={32}></Input>
        </InputGroup>
        <div className='row-right'>
          <FormPrimaryButton onClick={handleUsername} text={'Dalej'} icon={<ArrowRight className='icon-black'/>}/>
        </div>
      </div>
    )
  }

  if (isLogin) {
    function handleLogin() {
      const input_pwd = passwordEl.current.value;
      if (input_pwd.length < 5) return;

      (async () => {
        const req = await fetch(import.meta.env.VITE_API + "account/login", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username,
            password: input_pwd
          })
        });
        
        const resp = await req.json();
        if (resp.status == false) return;

        const clientId = resp.content;
        localStorage.setItem("client_id", clientId);
        localStorage.setItem("username", username);
        close(false);
        location.reload();
      })();
    }

    return (
      <div className='identification-step'>
        <span className='info-text'>
          <b>Znaleziono konto</b> o tej nazwie użytkownika, zaloguj się:
        </span>
        <InputGroup>
          <InputLabel><LockKeyholeIcon />Hasło</InputLabel>
          <Input ref={passwordEl} placeholder={'*****'} minlen={5} type="password"></Input>
        </InputGroup>
        <div className='row-right'>
          <FormSecondaryButton onClick={() => {setUsername(null)}} text={'Powrót'} />
          <FormPrimaryButton onClick={handleLogin} text={'Zaloguj się'} icon={<ArrowRight className='icon-black' />} />
        </div>
      </div>
    )
  }

  if (!isLogin) {
    function handleRegister() {
      const input_pwd = passwordEl.current.value;
      const input_repeat_pwd = passwordRepeatEl.current.value;
      if (input_pwd.length < 5) return;
      if (input_pwd != input_repeat_pwd) return

      (async () => {
        const req = await fetch(import.meta.env.VITE_API + "account/register", {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            client_id: localStorage.getItem("client_id") || '',
            username: username,
            password: input_pwd
          })
        });

        const resp = await req.json();
        if (resp.status == false) return;

        const clientId = resp.content;
        localStorage.setItem("client_id", clientId);
        localStorage.setItem("username", username);
        close(false);
        location.reload();
      })();
    }

    return (
      <div className='identification-step'>
        <span className='info-text'>
          <b>Nie znaleziono konta</b> o tej nazwie użytkownika, zarejestruj się:
        </span>
        <InputGroup>
          <InputLabel><LockKeyholeIcon />Hasło</InputLabel>
          <Input ref={passwordEl} placeholder={'*****'} minlen={5} type="password"></Input>
        </InputGroup>
        <InputGroup>
          <InputLabel><LockKeyholeIcon />Powtórz hasło</InputLabel>
          <Input ref={passwordRepeatEl} placeholder={'*****'} minlen={5} type="password"></Input>
        </InputGroup>
        <div className='row-right'>
          <FormSecondaryButton onClick={() => { setUsername(null) }} text={'Powrót'} />
          <FormPrimaryButton onClick={handleRegister} text={'Zarejestruj się'} icon={<ArrowRight className='icon-black' />} />
        </div>
      </div>
    )
  }

}


function AnonAccount({ close }) {
  return (
    <div className='account-content-container'>
      <span className='sub-panel info-text'>
        <b>Nie jesteś zalogowany</b>, ale twój progres <b>jest tymczasowo zapisany</b>. <br/>
        Utwórz konto, aby przenieść swój postęp i móc kontunuować naukę z innych urządzeń.
      </span>
      <div className='modal-sep'></div>

      <p className='action-text'>Zaloguj się lub zarejestruj:</p>
      <div className='identificaiton-process sub-panel'>
        <IdentificationProcess close={close}/>
      </div>
    </div>
  )
}

function UserAccount({}) {
  function logout() {
    (async () => {
      const req = await fetch(import.meta.env.VITE_API + "account/logout/" + localStorage.getItem('client_id'));
      const resp = await req.json();

      localStorage.setItem("client_id", '');
      localStorage.setItem("username", '');
      close(false);
      location.reload();
    })();
  }

  
  return (
    <div className='account-content-container'>
      <div className='modal-sep'></div>
      <p className='action-text'>Jesteś zalogowany jako: </p>
      <p className='info-text sub-panel'><b>{localStorage.getItem('username')}</b></p>
      <div className='modal-sep'></div>
      <FormSecondaryButton onClick={logout} text={"Wyloguj się"} icon={<ArrowRight className='icon'/>}></FormSecondaryButton>
    </div>
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
    return <AnonAccount close={closeView}/>
  }
}
