import React from 'react';
import ReactDOM from 'react-dom';
import { EGNavbar } from './components/navbars.js';
import '../static/stylesheets/reporting_app.css';


class MainPage extends React.Component {
    render() {
        return (
            <div>
                <EGNavbar />
                <p>
                Welcome to the Edinburgh Genomics Reporting App. Here, you can view QC data for pipeline runs,
                sequencing runs, samples and projects. Select a view from the toolbar above.
                </p>
            </div>
        )
    }
}

ReactDOM.render(<MainPage />, document.getElementById('app'));
