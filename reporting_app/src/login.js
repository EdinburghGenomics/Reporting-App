import React from 'react';
import ReactDOM from 'react-dom';
import { MinimalNavbar } from './components/navbars.js';
import '../static/stylesheets/reporting_app.css';


class LoginForm extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            urlSearchParams: new URLSearchParams(document.location.search),
        }
    }

    render() {
        const login_source = this.state.urlSearchParams.get('source');

        var msg = 'Welcome to the EGCG Reporting App. Log in here.';
        if (login_source == 'login_failed') {
            msg = 'Bad login';
        } else if (login_source == 'logged_out') {
            msg = 'Logged out'
        }

        return (
            <div>
                <p>{ msg }</p>
                <form action="login" method="POST">
                    <input type="text" name="username" id="username" placeholder="username"/>
                    <input type="password" name="pw" id="pw" placeholder="password"/>
                    <input type="submit" name="submit"/>
                </form>
            </div>
        )
    }
}

class Login extends React.Component {
    render() {
        return (
            <div>
                <MinimalNavbar />
                <LoginForm />
            </div>
        )
    }
}

ReactDOM.render(<Login />, document.getElementById('app'));
