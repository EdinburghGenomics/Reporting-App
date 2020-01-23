import React from 'react';
import { Navbar, NavbarBrand, Nav, NavItem, NavLink, UncontrolledDropdown, DropdownToggle, DropdownMenu, DropdownItem } from 'reactstrap';
import 'bootstrap/dist/css/bootstrap.min.css';


class EGNavLogo extends React.Component {
    render() {
        return <NavbarBrand href="/"><img style={{height: "28px"}} src="/static/img/EG_logo_final_version_colourwhite_cropped_white.svg" /></NavbarBrand>
    }
}


export class MinimalNavbar extends React.Component {
    render() {
        return (
            <div>
                <Navbar color="dark" dark expand="md">
                    <EGNavLogo />
                </Navbar>
            </div>
        )
    }
}

export class EGNavbar extends React.Component {
    render() {
        return (
            <div>
                <Navbar color="dark" dark expand="md">
                    <EGNavLogo />
                    <Nav className="ml-auto" navbar>
                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>Runs</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/runs/recent">Recent</a></DropdownItem>
                                <DropdownItem><a href="/runs/current_year">Current year</a></DropdownItem>
                                <DropdownItem><a href="/runs/last_12_months">Last 12 months</a></DropdownItem>
                                <DropdownItem><a href="/runs/all">All</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>

                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>Samples</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/samples/all">All</a></DropdownItem>
                                <DropdownItem><a href="/samples/processing">Processing</a></DropdownItem>
                                <DropdownItem><a href="/samples/toreview">To review</a></DropdownItem>
                                <DropdownItem><a href="/samples/notprocessing">Not processing</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>

                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>Projects</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/projects">Summary</a></DropdownItem>
                                <DropdownItem><a href="/projects/SGP">SGP Projects</a></DropdownItem>
                                <DropdownItem divider />
                                <DropdownItem><a href="/project_status/">Project Status - Open</a></DropdownItem>
                                <DropdownItem><a href="/project_status/lastweek">Project Status - Last Week</a></DropdownItem>
                                <DropdownItem><a href="/project_status/closed">Project Status - Closed</a></DropdownItem>
                                <DropdownItem><a href="/project_status/all">Project Status - All</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>

                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>Libraries</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/libraries/recent">Recent</a></DropdownItem>
                                <DropdownItem><a href="/libraries/current_year">Current year</a></DropdownItem>
                                <DropdownItem><a href="/libraries/last_12_months">Last 12 months</a></DropdownItem>
                                <DropdownItem><a href="/libraries/all">All</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>

                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>Genotyping</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/genotypes/recent">Recent</a></DropdownItem>
                                <DropdownItem><a href="/genotypes/current_year">Current year</a></DropdownItem>
                                <DropdownItem><a href="/genotypes/last_12_months">Last 12 months</a></DropdownItem>
                                <DropdownItem><a href="/genotypes/all">All</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>

                        <NavLink href="/species">Species</NavLink>
                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>Charts</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/charts/tat">Turnaround metrics</a></DropdownItem>
                                <DropdownItem><a href="/charts/bioinformatics">Bioinformatics pipeline activity</a></DropdownItem>
                                <li class="dropdown-header"><b>Sequencing metrics</b></li>
                                <DropdownItem><a href="/charts/seq/last_month">Last 30 days</a></DropdownItem>
                                <DropdownItem><a href="/charts/seq/last_3_months">Last 3 months</a></DropdownItem>
                                <DropdownItem><a href="/charts/seq/last_12_months">Last 12 months</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>

                        <UncontrolledDropdown nav inNavbar>
                            <DropdownToggle nav caret>{ window.user }</DropdownToggle>
                            <DropdownMenu right>
                                <DropdownItem><a href="/change_password">Change password</a></DropdownItem>
                                <DropdownItem><a href="/logout">Logout</a></DropdownItem>
                            </DropdownMenu>
                        </UncontrolledDropdown>
                    </Nav>
                </Navbar>
            </div>
        )
    }
}
