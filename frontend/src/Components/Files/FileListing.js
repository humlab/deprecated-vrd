import React from 'react';
import PropTypes from 'prop-types';

const FileListing = ({ filename, state }) => (
    <tr>
      <th scope="row">{filename}</th>
      <td>{state}</td>
    </tr>
  );
  
  FileListing.propTypes = {
    filename: PropTypes.string.isRequired,
    state: PropTypes.string.isRequired
  };

  
  export default FileListing;
  