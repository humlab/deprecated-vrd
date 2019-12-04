import React from 'react';
import PropTypes from 'prop-types';

import styled from 'styled-components';
import { useTable, useRowSelect } from 'react-table';

const Styles = styled.div`
  padding: 1rem;

  table {
    border-spacing: 0;
    border: 1px solid black;

    tr {
      :last-child {
        td {
          border-bottom: 0;
        }
      }
    }

    th,
    td {
      margin: 0;
      padding: 0.5rem;
      border-bottom: 1px solid black;
      border-right: 1px solid black;

      :last-child {
        border-right: 0;
      }
    }
  }
`;

function Table({ caption, columns, data, onRowSelect }) {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
    selectedFlatRows,
    state: { selectedRowPaths }
  } = useTable(
    {
      columns,
      data,
      debug: true
    },
    useRowSelect
  );

  return (
    <>
      <table {...getTableProps()}>
        <caption>{caption}</caption>
        <thead>
          {headerGroups.map((headerGroup, i) => (
            <tr {...headerGroup.getHeaderGroupProps()} key={i}>
              {headerGroup.headers.map((column, j) => (
                <th {...column.getHeaderProps()} key={j}>
                  {column.render('Header')}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.slice(0, 10).map((row, i) => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()} key={i}>
                {row.cells.map((cell, j) => {
                  return (
                    <td {...cell.getCellProps()} key={j}>
                      {cell.render('Cell')}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      {/* TODO: Attach to proper hook, calls every time on re-render atm*/}
      {onRowSelect(selectedFlatRows)}
      <p>Selected Rows: {selectedRowPaths.length}</p>
      <pre>
        <code>
          {JSON.stringify(
            {
              selectedRowPaths: [...selectedRowPaths.values()],
              'selectedFlatRows[].original': selectedFlatRows.map(
                d => d.original
              )
            },
            null,
            2
          )}
        </code>
      </pre>
    </>
  );
}

Table.propTypes = {
  caption: PropTypes.string.isRequired,
  columns: PropTypes.object.isRequired,
  data: PropTypes.object.isRequired,
  onRowSelect: PropTypes.func.isRequired
};

function FileTable({ caption, onRowSelect, data }) {
  const columns = React.useMemo(
    () => [
      // Let's make a column for selection
      {
        id: 'selection',
        // TODO: Support selecting all rows
        /*
        // The header can use the table's getToggleAllRowsSelectedProps method
        // to render a checkbox
        Header: ({ getToggleAllRowsSelectedProps }) => (
          <div>
            <input type="checkbox" {...getToggleAllRowsSelectedProps()} />
          </div>
        ),
        */
        // The cell can use the individual row's getToggleRowSelectedProps method
        // to the render a checkbox
        // eslint-disable-next-line react/prop-types, react/display-name
        Cell: ({ row }) => (
          <div>
            {/* eslint-disable-next-line react/prop-types */}
            <input type="checkbox" {...row.getToggleRowSelectedProps()} />
          </div>
        )
      },
      {
        Header: 'Name',
        columns: [
          {
            Header: 'Video Name',
            accessor: 'video_name'
          }
        ]
      },
      {
        Header: 'Info',
        columns: [
          {
            Header: 'Type',
            accessor: 'type'
          },
          {
            Header: 'Processing State',
            accessor: 'processing_state'
          }
        ]
      }
    ],
    []
  );

  return (
    <Styles>
      <Table
        caption={caption}
        columns={columns}
        data={data}
        onRowSelect={onRowSelect}
      />
    </Styles>
  );
}

FileTable.propTypes = {
  caption: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
  onRowSelect: PropTypes.func.isRequired
};

export default FileTable;
