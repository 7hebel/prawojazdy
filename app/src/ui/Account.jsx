import './Account.css';


function AnonAccount({}) {
  // info: data saved, register to persistent
  // register form / login form
  // reset progress btn
}

function UserAccount({}) {
  // show account data
  // logout btn
  // reset progress btn
}

export function AccountView({ closeView }) {
  const isAnon = localStorage.getItem("username") === null;
  
  return <h1>hello</h1>
}
