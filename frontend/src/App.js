import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';

import 'react-toastify/dist/ReactToastify.min.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'react-dropzone-uploader/dist/styles.css';

import Container from '@material-ui/core/Container';
import Header from './components/layout/Header';
import Main from './components/pages/Main';

export default function App() {
  return (
    <div className="app">
      <Router>
        <Header />
        <Container>
          <Switch>
            <Route exact path="/" component={Main} />
          </Switch>
        </Container>
      </Router>
    </div>
  );
}
