import React from 'react';
import PropTypes from 'prop-types';

import { useTable, useRowSelect } from 'react-table';

import CssBaseline from '@material-ui/core/CssBaseline'
import MaUTable from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableHead from '@material-ui/core/TableHead'
import TableRow from '@material-ui/core/TableRow'

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
      <MaUTable {...getTableProps()}>
        <caption>{caption}</caption>
        <TableHead>
          {headerGroups.map((headerGroup, i) => (
            <TableRow {...headerGroup.getHeaderGroupProps()} key={i}>
              {headerGroup.headers.map((column, j) => (
                <TableCell {...column.getHeaderProps()} key={j}>
                  {column.render('Header')}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableHead>
        <TableBody {...getTableBodyProps()}>
          {rows.map((row, i) => {
            prepareRow(row);
            return (
              <TableRow {...row.getRowProps()} key={i}>
                {row.cells.map((cell, j) => {
                  return (
                    <TableCell {...cell.getCellProps()} key={j}>
                      {cell.render('Cell')}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </MaUTable>
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
    <div>
      <CssBaseline />
      <Table
        caption={caption}
        columns={columns}
        data={data}
        onRowSelect={onRowSelect}
      />
    </div>
  );
}

FileTable.propTypes = {
  caption: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
  onRowSelect: PropTypes.func.isRequired
};

export default FileTable;
