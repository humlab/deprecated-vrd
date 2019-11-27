import React from 'react';
import PropTypes from 'prop-types';

import FileListing from './FileListing';

const FileTable = ({ files }) => (
  <div className="files">
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Name</th>
          <th scope="col">State</th>
        </tr>
      </thead>
      <tbody>
        {Object.keys(files).map((file, i) => (
          <FileListing key={i} filename={file} state={files[file]} />
        ))}
      </tbody>
    </table>
  </div>
);

FileTable.propTypes = {
  files: PropTypes.object.isRequired
};

export default FileTable;
